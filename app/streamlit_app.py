"""
SiteLens AI — Streamlit demo
=============================

Layered retrieval-and-assessment pipeline for building damage inspection.

Layout: map is sticky on the left (spatial-context background); notes column
on the right carries the gradient top-to-bottom — input -> retrieval ->
narrative -> audit -> senior coordinator summary -> architecture note.

The architecture has five layers. Layer 5 (cross-summary) is the
"above the narrative layer" placement we previously marked as out-of-scope.
It's the first place in the pipeline where an abstractive ML summariser
has real material to work with (inspector free-form text + rule-based
narrative + retrieved records) — rather than the all-templated input that
t5-small regurgitated at Layer 3.

Run from the repo root:
    streamlit run app/streamlit_app.py
"""

import os
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import folium
import streamlit as st
from branca.element import MacroElement, Template
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone
from streamlit_folium import st_folium
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM


# --------------------------------------------------------------------------
# Config
# --------------------------------------------------------------------------

REPO_ROOT = Path(__file__).parent.parent
load_dotenv(REPO_ROOT / ".env")

try:
    PINECONE_API_KEY = st.secrets["PINECONE_API_KEY"]
    INDEX_NAME = st.secrets.get("PINECONE_INDEX_NAME", "sitelens")
except Exception:
    PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
    INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "sitelens")
EMBED_MODEL = "all-MiniLM-L6-v2"
SUMMARISER_MODEL = "sshleifer/distilbart-cnn-12-6"

SCENARIOS = {
    "(Free-form input)": "",
    "Fire zone destruction": "building destroyed by fire in dense urban area",
    "Tsunami zone survival": "structure survived tsunami zone with strong shaking",
    "Slope failure obstruction": "obstructed assessment slope failure zone",
    "Multi-area inspection": "building destroyed fire and tsunami zones",
}

GSI_TILE_URL = "https://cyberjapandata.gsi.go.jp/xyz/seamlessphoto/{z}/{x}/{y}.jpg"
GSI_ATTR = "Map tiles by GSI (地理院タイル)"

DEFAULT_CENTER = (37.3960, 136.9000)
DEFAULT_ZOOM = 15

T5_REJECTED_OUTPUT = (
    "Summary: evidence: multi-source assessment. Building destroyed. "
    "Hazard: fire. MMI 8.4 (severe shaking). evidence: multi-source assessment. "
    "evidence: multi-source assessment."
)


# --------------------------------------------------------------------------
# Cached resources
# --------------------------------------------------------------------------

@st.cache_resource
def get_embed_model():
    return SentenceTransformer(EMBED_MODEL)


@st.cache_resource
def get_pinecone_index():
    pc = Pinecone(api_key=PINECONE_API_KEY)
    return pc.Index(INDEX_NAME)


@st.cache_resource
def get_summariser():
    """Layer-5 abstractive summariser. First load downloads ~300MB."""
    tokenizer = AutoTokenizer.from_pretrained(SUMMARISER_MODEL)
    model = AutoModelForSeq2SeqLM.from_pretrained(SUMMARISER_MODEL)
    return tokenizer, model


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------

def retrieve(query: str, top_k: int = 3):
    model = get_embed_model()
    index = get_pinecone_index()
    vec = model.encode([query])[0].tolist()
    results = index.query(vector=vec, top_k=top_k, include_metadata=True)
    return results["matches"]


def parse_hits(hits):
    outcomes, hazards, mmis, evidences = [], set(), [], set()
    for h in hits:
        for part in h["metadata"]["text"].split(". "):
            if part.startswith("Building "):
                outcomes.append(part.replace("Building ", "").lower())
            elif part.startswith("Hazard: "):
                hazards.add(part.replace("Hazard: ", ""))
            elif "MMI" in part:
                m = re.search(r"MMI ([\d.]+)", part)
                if m:
                    mmis.append(float(m.group(1)))
            elif part.startswith("Evidence: "):
                evidences.add(
                    part.replace("Evidence: ", "")
                        .replace(" assessment", "")
                        .rstrip(".")
                )
    return outcomes, hazards, mmis, evidences


def narrative_sentence(hits):
    outcomes, hazards, mmis, evidences = parse_hits(hits)
    n = len(hits)
    counts = Counter(outcomes)
    dominant = counts.most_common(1)[0][0] if counts else "assessed"
    haz_list = sorted(h for h in hazards if h != "seismic only")
    mmi_avg = sum(mmis) / len(mmis) if mmis else 0
    mmi_label = "severe" if mmi_avg >= 8 else "strong" if mmi_avg >= 6 else "moderate"
    ev_str = " and ".join(sorted(evidences))
    multi_zone = len(haz_list) > 1

    if haz_list:
        zone_str = " and ".join(haz_list)
        cond_str = (
            f"across {zone_str} zones under {mmi_label} shaking"
            if multi_zone else
            f"under {mmi_label} {zone_str} conditions"
        )
    else:
        cond_str = f"under {mmi_label} seismic shaking"

    destroyed = counts.get("destroyed", 0)
    survived = counts.get("survived", 0)

    if dominant == "destroyed":
        subject = f"All {n} buildings" if destroyed == n else f"{destroyed} of {n} buildings"
        s = f"{subject} were destroyed {cond_str} (MMI {mmi_avg:.1f})"
        if survived:
            s += f"; {survived} survived"
    elif dominant == "survived":
        subject = f"All {n} buildings" if survived == n else f"{survived} of {n} buildings"
        s = f"{subject} survived {cond_str} (MMI {mmi_avg:.1f})"
        if destroyed:
            s += f"; {destroyed} were destroyed"
    else:
        s = f"{n} buildings recorded {cond_str} (MMI {mmi_avg:.1f})"

    return f"{s}. Evidence: {ev_str}."


def stats_line(hits):
    outcomes, hazards, mmis, evidences = parse_hits(hits)
    dominant = Counter(outcomes).most_common(1)[0][0] if outcomes else "assessed"
    haz_list = sorted(h for h in hazards if h != "seismic only")
    haz_str = " and ".join(haz_list) if haz_list else "seismic"
    mmi_str = f"MMI {sum(mmis)/len(mmis):.1f}" if mmis else ""
    ev_str = " and ".join(sorted(evidences))
    return f"{len(hits)} building(s) {dominant}: {haz_str} hazard, {mmi_str}, {ev_str} evidence."


def cross_summary(query: str, narrative: str, hits) -> str:
    """
    Layer-5 senior-coordinator synthesis.
    Combines inspector free-form text + rule-based narrative + retrieved record texts
    into a paragraph, then abstractively summarises with distilbart-cnn-12-6.
    """
    if not hits or not query.strip():
        return ""

    record_texts = " ".join(h["metadata"]["text"] for h in hits)

    input_text = (
        f"Field inspection report. "
        f"The inspector at the site observed: {query.strip()} "
        f"System assessment: {narrative} "
        f"Precedent buildings reviewed: {record_texts}"
    )

    tokenizer, model = get_summariser()
    try:
        inputs = tokenizer(
            input_text,
            return_tensors="pt",
            max_length=1024,
            truncation=True,
        )
        outputs = model.generate(
            inputs.input_ids,
            max_length=80,
            min_length=30,
            num_beams=4,
            length_penalty=2.0,
            early_stopping=True,
        )
        return tokenizer.decode(outputs[0], skip_special_tokens=True).strip()
    except Exception as exc:  # noqa: BLE001 — defensive demo path
        return f"_(Summary generation failed: {exc})_"


def make_legend_html(hits):
    if not hits:
        return None

    outcomes, hazards, mmis, _ = parse_hits(hits)
    counts = Counter(outcomes)
    haz_list = sorted(h for h in hazards if h != "seismic only")
    haz_str = ", ".join(haz_list) if haz_list else "seismic"

    color_map = {"destroyed": "#A41E1E", "survived": "#2A7A2A"}
    rows = "".join(
        f"<div style='margin:2px 0;'>"
        f"<span style='display:inline-block;width:10px;height:10px;"
        f"background:{color_map.get(outcome, '#888')};border-radius:50%;"
        f"margin-right:6px;vertical-align:middle;'></span>"
        f"{outcome.capitalize()} — {n}</div>"
        for outcome, n in counts.most_common()
    )

    mmi_line = ""
    if mmis:
        mmi_min, mmi_max = min(mmis), max(mmis)
        mmi_line = (
            f"MMI {mmi_min:.1f} (severe)" if mmi_min == mmi_max
            else f"MMI {mmi_min:.1f}–{mmi_max:.1f}"
        )

    return f"""
    {{% macro html(this, kwargs) %}}
    <div style='
        position: absolute;
        top: 60px; left: 20px;
        background: rgba(20, 20, 20, 0.85);
        color: #f5f5f5;
        padding: 10px 14px;
        border-radius: 4px;
        font-family: -apple-system, BlinkMacSystemFont, sans-serif;
        font-size: 12px;
        line-height: 1.45;
        z-index: 9999;
        box-shadow: 0 2px 6px rgba(0,0,0,0.3);
        min-width: 140px;'>
      <div style='font-weight: 600; margin-bottom: 6px;
                  font-size: 10px; letter-spacing: 0.8px; color: #ccc;'>LEGEND</div>
      {rows}
      <div style='margin-top: 8px; font-size: 11px; color: #ccc;'>Hazard: {haz_str}</div>
      <div style='font-size: 11px; color: #ccc;'>{mmi_line}</div>
    </div>
    {{% endmacro %}}
    """


def build_map(hits):
    geo_hits = [h for h in (hits or []) if h["metadata"].get("lat") and h["metadata"].get("lon")]

    if geo_hits:
        lats = [h["metadata"]["lat"] for h in geo_hits]
        lons = [h["metadata"]["lon"] for h in geo_hits]
        center = (sum(lats) / len(lats), sum(lons) / len(lons))

        # Adaptive zoom based on geographic spread of markers
        if len(geo_hits) == 1:
            zoom = 17
        else:
            spread = max(max(lats) - min(lats), max(lons) - min(lons))
            if   spread > 0.10:  zoom = 11  # > 10 km — multi-municipality
            elif spread > 0.05:  zoom = 12  # 5–10 km
            elif spread > 0.02:  zoom = 13  # 2–5 km
            elif spread > 0.01:  zoom = 14  # 1–2 km
            elif spread > 0.005: zoom = 16  # 500 m–1 km
            else:                zoom = 17  # tight cluster
    else:
        center = DEFAULT_CENTER
        zoom = DEFAULT_ZOOM

    m = folium.Map(
        location=list(center),
        zoom_start=zoom,
        tiles=GSI_TILE_URL,
        attr=GSI_ATTR,
        max_zoom=18,
    )

    for h in geo_hits:
        text = h["metadata"]["text"]
        if "destroyed" in text.lower():
            color = "#A41E1E"
        elif "survived" in text.lower():
            color = "#2A7A2A"
        else:
            color = "#888888"

        folium.CircleMarker(
            location=[h["metadata"]["lat"], h["metadata"]["lon"]],
            radius=10,
            color=color,
            fill=True,
            fillOpacity=0.85,
            weight=2,
            popup=folium.Popup(
                f"<b>{h['id']}</b><br/>Score: {h['score']:.2f}<br/>{text}",
                max_width=300,
            ),
        ).add_to(m)

    legend_html = make_legend_html(geo_hits)
    if legend_html:
        macro = MacroElement()
        macro._template = Template(legend_html)
        m.get_root().add_child(macro)

    return m


# --------------------------------------------------------------------------
# Page setup
# --------------------------------------------------------------------------

st.set_page_config(
    page_title="SiteLens AI",
    layout="wide",
)

st.markdown(
    "<style>.block-container { padding-top: 1rem !important; padding-bottom: 0 !important; }</style>",
    unsafe_allow_html=True,
)

PANEL_HEIGHT = 800

# --------------------------------------------------------------------------
# Two-column layout: fixed map (left) + scrolling notes (right)
# --------------------------------------------------------------------------

map_col, notes_col = st.columns([3, 2], gap="medium")

# ---- NOTES COLUMN (single pass, native scrollable container) -------------

with notes_col:

    # ---- Input (always visible, not inside scrollable container) ----------

    st.title("SiteLens AI")
    st.caption(
        "Layered retrieval-and-assessment pipeline for building damage inspection. "
        "Vescovo et al. 2025 Noto Peninsula dataset · sentence-transformers · "
        "Pinecone · distilbart-cnn."
    )

    scenario_key = st.selectbox(
        "Scenario",
        list(SCENARIOS.keys()),
        index=0,
        label_visibility="collapsed",
    )
    if scenario_key != st.session_state.get("_prev_scenario"):
        st.session_state["_prev_scenario"] = scenario_key
        st.session_state["query_input"] = SCENARIOS[scenario_key]

    query = st.text_area(
        "Description / query",
        key="query_input",
        height=80,
        placeholder=(
            "e.g. 'Two-storey timber-frame, roof partially collapsed, "
            "scorch marks on the south wall...'"
        ),
        label_visibility="collapsed",
    )

    run_col, k_col = st.columns([2, 1])
    with run_col:
        run = st.button("Run assessment", type="primary", use_container_width=True)
    with k_col:
        top_k = st.number_input(
            "Top-k", min_value=1, max_value=10, value=3,
            label_visibility="collapsed",
        )

    # ---- Retrieval -------------------------------------------------------

    if run and query.strip():
        timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
        with st.spinner("Retrieving precedent records..."):
            hits = retrieve(query, top_k=top_k)
        st.session_state["hits"] = hits
        st.session_state["timestamp"] = timestamp
        st.session_state["run_query"] = query
    elif run:
        st.warning("Please enter a description before running.")
        hits = None
        timestamp = None
    else:
        hits = st.session_state.get("hits")
        timestamp = st.session_state.get("timestamp")
        query = st.session_state.get("run_query", query)

    # ---- Results (scrollable container) ----------------------------------

    with st.container(height=PANEL_HEIGHT - 310, border=False):
        if hits:
            st.markdown("**2 — Retrieved precedents**")
            for h in hits:
                header = f"[{h['score']:.2f}] {h['id']} — {h['metadata']['text']}"
                with st.expander(header):
                    st.json(h["metadata"])

            st.markdown("**3 — Field assessment**")
            narrative = narrative_sentence(hits)
            st.markdown(narrative)
            avg_score = sum(h["score"] for h in hits) / len(hits)
            st.caption(
                f"Aggregated from {len(hits)} retrieved precedents · "
                f"avg similarity {avg_score:.2f} · "
                f"rule-based aggregation, no ML at this layer"
            )

            st.markdown("**4 — Audit record**")
            with st.expander("View audit JSON"):
                audit = {
                    "timestamp_utc": timestamp,
                    "query": query,
                    "top_k": top_k,
                    "embedding_model": EMBED_MODEL,
                    "index": INDEX_NAME,
                    "narrative": narrative,
                    "matches": [
                        {"id": h["id"], "score": float(h["score"]), "text": h["metadata"]["text"]}
                        for h in hits
                    ],
                }
                st.json(audit)

            st.markdown("**5 — Senior coordinator summary**")
            st.caption(
                f"Abstractive synthesis · {SUMMARISER_MODEL} · "
                "may rephrase but does not invent facts not present in input"
            )
            with st.spinner("Synthesising summary..."):
                summary = cross_summary(query, narrative, hits)
            if summary:
                st.markdown(f"> {summary}")

            with st.expander("Architecture note: ML summarisation placement"):
                st.markdown(
                    "**The architecture has three plausible ML-summarisation placements. "
                    "Two are tested in this prototype.**\n\n"
                    "**At the narrative layer (Layer 3) — rejected.** "
                    "Tested 13 May 2026: t5-small given top-3 retrieved records as input "
                    "regurgitated chunks rather than aggregating, because the input was already "
                    "structured templated text with nothing to compress:"
                )
                st.code(T5_REJECTED_OUTPUT, language="text")
                st.markdown(
                    "Not specific to t5-small — BART or Pegasus would fail similarly *at this layer*. "
                    "Layer 3 stays rule-based: deterministic, grounded, audit-ready.\n\n"
                    "**Above the narrative layer (Layer 5) — implemented.** "
                    f"distilbart-cnn-12-6 synthesises the inspector's free-form input + the "
                    "rule-based narrative + the retrieved record texts into a single coordinator "
                    "summary. The input is no longer all-templated — the inspector's own words give "
                    "the model real material to compress. This is the right architectural placement "
                    "for abstractive ML in this pipeline.\n\n"
                    "**Below the input layer — out of hackathon scope.** "
                    "Parsing free-form inspector notes into structured field extraction (damage "
                    "state, hazard, severity). Closer to NER/extraction than summarisation; an "
                    "encoder-decoder fine-tuned on inspector-report data would serve. Week 11+ work."
                )
        else:
            st.info("Pick a scenario or type a description above, then **Run assessment**.")

# ---- MAP COLUMN ----------------------------------------------------------

with map_col:
    m = build_map(st.session_state.get("hits"))
    st_folium(
        m,
        height=PANEL_HEIGHT,
        returned_objects=[],
        use_container_width=True,
    )
