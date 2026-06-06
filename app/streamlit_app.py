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

import html
import os
os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import folium
from folium.plugins import MarkerCluster
import pandas as pd
import streamlit as st
from branca.element import MacroElement, Template
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone
from streamlit_folium import st_folium

from transformers.utils import logging as _hf_logging
_hf_logging.disable_progress_bar()

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.translation.audience_translator import translate


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

try:
    os.environ["GEMINI_API_KEY"] = st.secrets["GEMINI_API_KEY"]
except Exception:
    pass  # falls through to os.environ already set via .env
EMBED_MODEL = "all-MiniLM-L6-v2"

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



@st.cache_data
def load_labels() -> pd.DataFrame:
    path = REPO_ROOT / "data" / "noto_crops" / "labels.csv"
    return pd.read_csv(path, index_col="s_fid")


@st.cache_data
def load_predictions() -> dict:
    """Pre-computed CNN outputs from model/evaluate.py. No model runs in the app."""
    path = REPO_ROOT / "data" / "noto_crops" / "predictions.csv"
    df = pd.read_csv(path, dtype={"s_fid": str}).set_index("s_fid")
    return df.to_dict("index")   # {s_fid: {true_label, pred_prob, pred_label}}


@st.cache_data
def load_display() -> dict:
    """Readable label parts per building, keyed by string s_fid.
    Stable 'Bldg N' from sorted s_fid; municipality + coords for context."""
    df = pd.read_csv(REPO_ROOT / "data" / "noto_crops" / "labels.csv", dtype={"s_fid": str})
    df["_n"] = pd.to_numeric(df["s_fid"], errors="coerce")
    df = df.sort_values(["_n", "s_fid"]).reset_index(drop=True)
    out = {}
    for i, row in df.iterrows():
        parts = str(row.get("municipality", "")).strip().split("、")
        city  = parts[1] if len(parts) >= 2 else (parts[0] if parts else "Noto")
        out[str(row["s_fid"])] = {"bldg": i + 1, "muni": city or "Noto"}
    return out


def display_name(s_fid: str) -> str:
    info = load_display().get(str(s_fid))
    return f"{info['muni']} · Bldg {info['bldg']:04d}" if info else f"Bldg {s_fid}"


@st.cache_data
def all_buildings_geojson() -> dict:
    """All buildings as one GeoJSON layer (cheap to serialise vs N markers)."""
    df = load_labels().reset_index()
    disp = load_display()
    feats = []
    for _, row in df.iterrows():
        sid = str(row["s_fid"])
        lat, lon = float(row.get("centroid_lat", 0)), float(row.get("centroid_lon", 0))
        if not lat or not lon:
            continue
        b = disp.get(sid, {}).get("bldg")
        feats.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [lon, lat]},
            "properties": {"bldg": f"Bldg {b:04d}" if b else sid},
        })
    return {"type": "FeatureCollection", "features": feats}


@st.cache_data
def bldg_index() -> dict:
    """Reverse map: building number -> s_fid."""
    return {info["bldg"]: sid for sid, info in load_display().items()}


def _row_to_text(row) -> str:
    outcome = "destroyed" if int(row["damage_val"]) > 0 else "survived"
    haz = []
    if int(row.get("gsi_fire", 0)):          haz.append("fire")
    if int(row.get("gsi_tsunami", 0)):       haz.append("tsunami")
    if int(row.get("gsi_slope_failure", 0)): haz.append("slope failure")
    hazard = ", ".join(haz) if haz else "seismic only"
    mmi = float(row.get("usgs_mmi", 0))
    sev = "severe shaking" if mmi >= 8 else "strong shaking" if mmi >= 6 else "moderate shaking"
    return (f"Building {outcome}. Hazard: {hazard}. "
            f"MMI {mmi:.1f} ({sev}). Evidence: multi-source assessment.")


def neighbours_by_distance(s_fid: str, k: int = 3):
    """Anchor + its k spatially nearest buildings (centroid distance).
    Hit-shaped; 'score' carries distance in metres (0 for the anchor)."""
    import math
    df = load_labels().reset_index()
    df["s_fid"] = df["s_fid"].astype(str)
    anchor = df[df["s_fid"] == str(s_fid)]
    if anchor.empty:
        return []
    alat = float(anchor.iloc[0]["centroid_lat"]); alon = float(anchor.iloc[0]["centroid_lon"])
    coslat = math.cos(math.radians(alat))
    df = df.assign(_m=(((df["centroid_lat"] - alat)) ** 2
                       + ((df["centroid_lon"] - alon) * coslat) ** 2) ** 0.5 * 111_320)
    nearest = df.sort_values("_m").head(k + 1)
    return [{
        "id": str(r["s_fid"]),
        "score": float(r["_m"]),
        "metadata": {"text": _row_to_text(r),
                     "lat": float(r["centroid_lat"]),
                     "lon": float(r["centroid_lon"])},
    } for _, r in nearest.iterrows()]


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------

def hit_to_record(hit_id: str) -> dict | None:
    df = load_labels()
    if hit_id not in df.index:
        return None
    row = df.loc[hit_id]
    record = {
        "s_fid":            hit_id,
        "municipality":     str(row.get("municipality", "")),
        "centroid_lat":     float(row.get("centroid_lat", 0)),
        "centroid_lon":     float(row.get("centroid_lon", 0)),
        "damage_val":       int(row.get("damage_val", 0)),
        "conf":             str(row.get("conf", "single")),
        "gsi_fire":         int(row.get("gsi_fire", 0)),
        "gsi_tsunami":      int(row.get("gsi_tsunami", 0)),
        "gsi_slope_failure":int(row.get("gsi_slope_failure", 0)),
        "usgs_mmi":         float(row.get("usgs_mmi", 0)),
    }
    pred = load_predictions().get(str(hit_id))
    if pred is not None:
        true_bin = int(record["damage_val"] > 0)
        record["pred_label"]   = int(pred["pred_label"])
        record["pred_prob"]    = float(pred["pred_prob"])
        record["pred_correct"] = (int(pred["pred_label"]) == true_bin)
    return record


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
    """Layer-5 senior-coordinator synthesis via Gemini 2.5 Flash."""
    if not hits or not query.strip():
        return ""
    from google import genai
    record_texts = " ".join(h["metadata"]["text"] for h in hits)
    prompt = (
        "You are a senior inspection coordinator. In 2–3 sentences synthesise the "
        "field report for a coordinator. Use only facts present; invent nothing.\n\n"
        f"Inspector observed: {query.strip()}\n"
        f"System assessment: {narrative}\n"
        f"Precedent buildings: {record_texts}"
    )
    try:
        resp = genai.Client().models.generate_content(
            model="gemini-2.5-flash", contents=prompt)
        return resp.text.strip()
    except Exception:
        return narrative


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


def build_map(hits, selected_id=None, map_center=None, map_zoom=None):
    geo_hits = [h for h in (hits or []) if h["metadata"].get("lat") and h["metadata"].get("lon")]

    if map_center is not None and map_zoom is not None:
        # Preserve user's current viewport (target selection, report generation)
        center = map_center
        zoom = map_zoom
    elif geo_hits:
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
        prefer_canvas=True,
    )

    # all buildings as a zoom-aware cluster: one bubble when far, individuals when close
    cluster = MarkerCluster(
        name="all buildings",
        options={"maxClusterRadius": 45, "disableClusteringAtZoom": 17,
                 "showCoverageOnHover": False, "spiderfyOnMaxZoom": False},
    )
    cluster.add_to(m)
    for feat in all_buildings_geojson()["features"]:
        lon, lat = feat["geometry"]["coordinates"]
        folium.CircleMarker(
            location=[lat, lon], radius=3, weight=1.5,
            color="#ffffff", fill=True, fill_color="#ffffff", fill_opacity=0.4,
            tooltip=feat["properties"]["bldg"],
        ).add_to(cluster)

    for h in geo_hits:
        text = h["metadata"]["text"]
        if "destroyed" in text.lower():
            color = "#A41E1E"
        elif "survived" in text.lower():
            color = "#2A7A2A"
        else:
            color = "#888888"

        is_selected = h["id"] == selected_id
        lat = h["metadata"]["lat"]
        lon = h["metadata"]["lon"]

        # pre-computed model call for this building (no model runs here)
        pred = load_predictions().get(str(h["id"]))
        pred_html = ""
        if pred is not None:
            names = {0: "survived", 1: "destroyed"}
            p_label = int(pred["pred_label"])
            gt = "destroyed" if "destroyed" in text.lower() else (
                 "survived" if "survived" in text.lower() else None)
            mark = "" if gt is None else (" ✓" if gt == names[p_label] else " ✗ miss")
            pred_html = (
                f"<br/><span style='font-size:11px;color:#555;'>"
                f"Model: <b>{names[p_label]}</b> "
                f"(P destroyed {float(pred['pred_prob']):.0%}){mark}</span>"
            )

        folium.CircleMarker(
            location=[lat, lon],
            radius=10,
            color="white" if is_selected else color,
            fill_color=color,
            fill=True,
            fillOpacity=0.85,
            weight=4 if is_selected else 2,
            popup=folium.Popup(
                f"<b style='font-size:12px'>{display_name(h['id'])}</b><br/>"
                f"Score: {h['score']:.2f}<br/>"
                f"<span style='font-size:11px'>{text}</span>"
                f"{pred_html}"
                f"<br/><span style='font-size:10px;color:#999;'>{lat:.4f}, {lon:.4f} · ref {h['id']}</span>",
                max_width=300,
            ),
        ).add_to(m)

    legend_html = make_legend_html(geo_hits)
    if legend_html:
        macro = MacroElement()
        macro._template = Template(legend_html)
        m.get_root().add_child(macro)

    return m, center, zoom


# --------------------------------------------------------------------------
# Page setup
# --------------------------------------------------------------------------

st.set_page_config(
    page_title="SiteLens AI",
    layout="wide",
)

st.markdown("""
<style>
div[data-testid="stCode"] pre {
    white-space: pre-wrap !important;
    word-wrap: break-word !important;
    overflow-x: hidden !important;
}
div[data-testid="stJson"] {
    overflow-x: auto;
}
button[kind="primary"] {
    background-color: #A41E1E !important;
    border-color: #A41E1E !important;
    color: white !important;
}
button[kind="primary"]:hover {
    background-color: #8B1818 !important;
    border-color: #8B1818 !important;
    color: white !important;
}
</style>
""", unsafe_allow_html=True)

st.markdown(
    "<style>.block-container { padding-top: 1rem !important; padding-bottom: 0 !important; }</style>",
    unsafe_allow_html=True,
)

PANEL_HEIGHT = 800

# --------------------------------------------------------------------------
# Two-column layout: fixed map (left) + scrolling notes (right)
# --------------------------------------------------------------------------

map_col, notes_col = st.columns([3, 2], gap="medium")

# ---- MAP COLUMN — runs first so click state is ready when notes_col renders

with map_col:
    # On the forced rerun after ASSESS, map_data["center"] is stale (previous position).
    # Pop the flag here so map_col knows to trust computed values, not map_data.
    _fit_all_this_run = st.session_state.pop("_fit_all_run", False)
    if _fit_all_this_run:
        st.session_state.pop("map_center", None)
        st.session_state.pop("map_zoom", None)

    m, _computed_center, _computed_zoom = build_map(
        st.session_state.get("hits"),
        selected_id=st.session_state.get("layer6_target_id"),
        map_center=st.session_state.get("map_center"),
        map_zoom=st.session_state.get("map_zoom"),
    )
    map_data = st_folium(
        m,
        height=PANEL_HEIGHT,
        returned_objects=[],
        use_container_width=True,
    )

    # Persist viewport so REPORT and target-dropdown changes don't rezoom.
    # Fit-all run: map_data is one run behind — trust computed values.
    # Other runs: store only when map_data reports a position that differs from
    # what we initialized (i.e. the user actually panned/zoomed).
    _raw_center = (map_data or {}).get("center")
    _raw_zoom   = (map_data or {}).get("zoom")
    if _fit_all_this_run:
        st.session_state["map_center"] = _computed_center
        st.session_state["map_zoom"]   = _computed_zoom
    elif _raw_center and _raw_zoom is not None:
        _dlat, _dlng = _raw_center["lat"], _raw_center["lng"]
        _clat, _clng = _computed_center
        if (abs(_dlat - _clat) > 1e-9
                or abs(_dlng - _clng) > 1e-9
                or abs(float(_raw_zoom) - float(_computed_zoom)) > 0.1):
            st.session_state["map_center"] = (_dlat, _dlng)
            st.session_state["map_zoom"]   = _raw_zoom

# ---- NOTES COLUMN --------------------------------------------------------

def _clear_query():
    if st.session_state.get("bldg_input", 0) > 0:
        st.session_state["query_input"] = ""

def _clear_bldg():
    if st.session_state.get("query_input", "").strip():
        st.session_state["bldg_input"] = 0

with notes_col:

    # ---- Input (always visible, not inside scrollable container) ----------

    st.title("SiteLens AI")
    st.caption(
        "Layered retrieval-and-assessment pipeline for building damage inspection. "
        "Vescovo et al. 2025 Noto Peninsula dataset · sentence-transformers · "
        "Pinecone · Gemini 2.5 Flash."
    )

    scen_col, k_col, run_col = st.columns([3, 0.7, 1.4])
    with scen_col:
        scenario_key = st.selectbox(
            "Scenario",
            list(SCENARIOS.keys()),
            index=0,
            label_visibility="collapsed",
        )
    with k_col:
        top_k = st.number_input(
            "Top-k", min_value=1, max_value=10, value=3,
            label_visibility="collapsed",
        )
    with run_col:
        run = st.button("ASSESS", type="primary", use_container_width=True)

    if scenario_key != st.session_state.get("_prev_scenario"):
        st.session_state["_prev_scenario"] = scenario_key
        st.session_state["query_input"] = SCENARIOS[scenario_key]
        st.session_state["bldg_input"] = 0

    bldg_num = st.number_input(
        "Pick a building number (optional — overrides the description)",
        min_value=0, max_value=len(load_display()), step=1,
        key="bldg_input", on_change=_clear_query,
        help="Type a Bldg number from the map to assess that exact building and its "
             "neighbours. Leave at 0 to use the description below.",
    )

    query = st.text_area(
        "Description / query",
        key="query_input",
        on_change=_clear_bldg,
        height=80,
        placeholder=(
            "e.g. 'Two-storey timber-frame, roof partially collapsed, "
            "scorch marks on the south wall...'"
        ),
        label_visibility="collapsed",
    )

    # ---- Retrieval -------------------------------------------------------

    if run and bldg_num > 0:
        sid = bldg_index().get(int(bldg_num))
        if sid is None:
            st.warning(f"Building {int(bldg_num)} not found.")
            hits, timestamp = None, None
        else:
            timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
            with st.spinner(f"Pulling {display_name(sid)} and its nearest buildings..."):
                hits = neighbours_by_distance(sid, k=top_k)
            st.session_state["hits"] = hits
            st.session_state["timestamp"] = timestamp
            st.session_state["run_query"] = f"[map selection] {display_name(sid)}"
            st.session_state["retrieval_mode"] = "spatial"
            st.session_state.pop("layer6_result", None)
            st.session_state["layer6_target_id"] = sid
            st.session_state["_fit_all_run"] = True
            st.rerun()
    elif run and query.strip():
        timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
        with st.spinner("Retrieving precedent records..."):
            hits = retrieve(query, top_k=top_k)
        st.session_state["hits"] = hits
        st.session_state["timestamp"] = timestamp
        st.session_state["run_query"] = query
        st.session_state["retrieval_mode"] = "semantic"
        st.session_state.pop("layer6_result", None)
        st.session_state.pop("layer6_target_id", None)
        st.session_state["_fit_all_run"] = True
        st.rerun()
    elif run:
        st.warning("Enter a description or pick a building number before running.")
        hits, timestamp = None, None
    else:
        hits = st.session_state.get("hits")
        timestamp = st.session_state.get("timestamp")
        query = st.session_state.get("run_query", query)

    # ---- Results (scrollable container) ----------------------------------

    with st.container(height=PANEL_HEIGHT - 260, border=False):
        if hits:
            st.markdown("**2 — Retrieved precedents**")
            mode = st.session_state.get("retrieval_mode", "semantic")
            for h in hits:
                tag = (("anchor" if h["score"] < 1 else f"{h['score']:.0f} m")
                       if mode == "spatial" else f"{h['score']:.2f}")
                header = f"[{tag}] {display_name(h['id'])} — {h['metadata']['text']}"
                with st.expander(header):
                    st.json(h["metadata"])

            st.markdown("**3 — Field assessment**")
            narrative = narrative_sentence(hits)
            st.markdown(narrative)
            if mode == "spatial":
                st.caption(f"Anchor + {len(hits)-1} nearest buildings by distance · "
                           "rule-based aggregation, no ML at this layer")
            else:
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
                "Abstractive synthesis · Gemini 2.5 Flash · "
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
                    "Gemini 2.5 Flash synthesises the inspector's free-form input + the "
                    "rule-based narrative + the retrieved record texts into a single coordinator "
                    "summary. The input is no longer all-templated — the inspector's own words give "
                    "the model real material to compress. This is the right architectural placement "
                    "for abstractive ML in this pipeline. (Originally distilbart-cnn-12-6; moved to "
                    "Gemini to stay within Streamlit Cloud's memory ceiling.)\n\n"
                    "**Below the input layer — out of hackathon scope.** "
                    "Parsing free-form inspector notes into structured field extraction (damage "
                    "state, hazard, severity). Closer to NER/extraction than summarisation; an "
                    "encoder-decoder fine-tuned on inspector-report data would serve. Week 11+ work."
                )
            st.markdown("**6 — Audience translation**")
            hit_ids = [h["id"] for h in hits]
            default_target = st.session_state.get("layer6_target_id", hit_ids[0])
            if default_target not in hit_ids:
                default_target = hit_ids[0]

            aud_col, tgt_col, gen_col = st.columns([2.5, 1.9, 1.4], vertical_alignment="bottom")
            with aud_col:
                audience = st.selectbox(
                    "Audience",
                    ["insurance", "engineering", "legal"],
                    format_func=lambda x: {
                        "insurance":   "Insurance adjuster (J-PIC)",
                        "engineering": "Structural engineer",
                        "legal":       "Legal counsel",
                    }[x],
                    key="layer6_audience",
                    label_visibility="collapsed",
                )
            with tgt_col:
                selected_target = st.selectbox(
                    "Target",
                    hit_ids,
                    index=hit_ids.index(default_target),
                    format_func=display_name,
                    key="layer6_target_sel",
                    label_visibility="collapsed",
                )
                st.session_state["layer6_target_id"] = selected_target
            with gen_col:
                run_report = st.button("REPORT", key="layer6_run", type="primary", use_container_width=True)
            if run_report:
                target_hit = next((h for h in hits if h["id"] == selected_target), hits[0])
                target_record = {"id": target_hit["id"], **target_hit["metadata"]}
                precedents = [
                    {
                        "id": h["id"],
                        "label": "destroyed" if "destroyed" in h["metadata"]["text"].lower() else "survived",
                        "similarity": h["score"],
                    }
                    for h in hits if h["id"] != target_hit["id"]
                ][:3]
                with st.spinner(f"Translating for {audience} audience..."):
                    result = translate(
                        record=target_record,
                        audience=audience,
                        precedents=precedents,
                        narrative=narrative,
                    )
                st.session_state["layer6_result"] = result

            if st.session_state.get("layer6_result"):
                result = st.session_state["layer6_result"]
                stale = result["record_s_fid"] != selected_target
                opacity = "0.35" if stale else "1"
                border_color = "#666" if stale else "#A41E1E"
                st.markdown(
                    f"""<div style="
                        background: var(--secondary-background-color);
                        color: var(--text-color);
                        border-left: 3px solid {border_color};
                        padding: 16px 20px;
                        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
                        font-size: 14px;
                        line-height: 1.6;
                        white-space: pre-wrap;
                        word-wrap: break-word;
                        border-radius: 4px;
                        opacity: {opacity};
                    ">{html.escape(result['output_text'])}</div>""",
                    unsafe_allow_html=True,
                )
                if stale:
                    st.caption(f"Report is for {display_name(result['record_s_fid'])} — hit REPORT to regenerate.")
                with st.expander("Translation audit"):
                    st.json({
                        "audience":     result["audience"],
                        "model":        result["model"],
                        "temperature":  result["temperature"],
                        "record_s_fid": result["record_s_fid"],
                        "user_content": result["user_content"],
                    })

            st.markdown("<div style='height: 80px'></div>", unsafe_allow_html=True)

        else:
            st.info("Pick a scenario or type a description above, then **Run assessment**.")

