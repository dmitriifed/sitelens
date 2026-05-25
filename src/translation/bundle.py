"""
bundle.py — assemble a record + context into prompt-ready text.

Layer 6 helper. Converts a per-building record plus optional retrieved
precedents and Layer 3 narrative into the user-content block consumed by
the audience translator.

Schema-resilient: accepts either the full Layer 1 schema (labels.csv) or
the Layer 2 sample-record schema (sample_records.json). Structured fields
(damage_val, gsi_*, usgs_mmi) take priority; the text field is parsed as
fallback when they are absent.
"""

import re
from typing import Optional


_PERIL_PRIORITY = ["fire", "tsunami", "slope_failure"]
_PERIL_FLAGS = {
    "fire":          "gsi_fire",
    "tsunami":       "gsi_tsunami",
    "slope_failure": "gsi_slope_failure",
}

# Deterministic audit reference. Held constant across runs so temperature-0.0
# outputs stay bit-identical for regression testing. Update on pipeline /
# dataset / imagery version bumps only.
_PIPELINE_VERSION = "SiteLens-v0.9-w10"
_AUDIT_REFERENCE = (
    f"{_PIPELINE_VERSION} / Vescovo2025 (DOI 10.5281/zenodo.11055711) / GSI 2024-01-11"
)


def _compute_next_action(record: dict) -> str:
    """Return the recommended next-action from damage_val alone."""
    return "field inspection" if record["damage_val"] == 1 else "desk approval"


def _compute_perils(record: dict) -> tuple[str, str]:
    """Return (primary_peril, secondary_peril) from hazard flags + damage_val."""
    if record["damage_val"] == 0:
        return "none (building survived)", "none (building survived)"

    active = [p for p in _PERIL_PRIORITY if record.get(_PERIL_FLAGS[p])]
    if not active:
        return "seismic", "none indicated"
    primary = active[0]
    secondary = active[1] if len(active) > 1 else "none indicated"
    return primary, secondary


def _normalise(record: dict) -> dict:
    """Extract a canonical field set from either corpus schema.

    Layer 1 (labels.csv): has damage_val, gsi_fire, gsi_tsunami,
      gsi_slope_failure, usgs_mmi, centroid_lat, centroid_lon, conf, s_fid.
    Layer 2 (sample_records.json via Pinecone metadata): has id, text,
      municipality, lat, lon — all structured fields absent.
    """
    text = record.get("text", "")
    text_lower = text.lower()

    # Identity
    record_id = (
        record.get("s_fid")
        or record.get("bldg_id")
        or record.get("id", "unknown")
    )
    munic = record.get("municipality", "Wajima (default)")

    # Coordinates — Layer 1 uses centroid_lat/lon; Layer 2 uses lat/lon
    lat = record.get("centroid_lat") or record.get("lat")
    lon = record.get("centroid_lon") or record.get("lon")

    # damage_val — structured field > label string > text parse
    if record.get("damage_val") is not None:
        damage_val = int(record["damage_val"])
    elif record.get("label"):
        damage_val = 1 if record["label"] == "destroyed" else 0
    elif "building destroyed" in text_lower:
        damage_val = 1
    else:
        damage_val = 0

    # conf
    conf = record.get("conf", "unspecified")

    # MMI — structured field > text parse
    if record.get("usgs_mmi") is not None:
        mmi = float(record["usgs_mmi"])
    elif record.get("mmi") is not None:
        mmi = float(record["mmi"])
    else:
        m = re.search(r"MMI ([\d.]+)", text)
        mmi = float(m.group(1)) if m else 0.0

    # Hazard flags — structured field > text parse
    fire    = int(record.get("gsi_fire",          1 if "hazard: fire"         in text_lower else 0))
    tsunami = int(record.get("gsi_tsunami",        1 if "tsunami"             in text_lower else 0))
    slope   = int(record.get("gsi_slope_failure",  1 if "slope failure"       in text_lower else 0))

    return {
        "record_id":  record_id,
        "munic":      munic,
        "lat":        lat,
        "lon":        lon,
        "damage_val": damage_val,
        "conf":       conf,
        "mmi":        mmi,
        "fire":       fire,
        "tsunami":    tsunami,
        "slope":      slope,
    }


def format_bundle(
    record: dict,
    precedents: Optional[list[dict]] = None,
    narrative: Optional[str] = None,
) -> str:
    """Build the user-content block for an audience translation call."""
    parts = []

    n = _normalise(record)

    primary_peril, secondary_peril = _compute_perils({
        "damage_val":        n["damage_val"],
        "gsi_fire":          n["fire"],
        "gsi_tsunami":       n["tsunami"],
        "gsi_slope_failure": n["slope"],
    })
    next_action = _compute_next_action({"damage_val": n["damage_val"]})

    parts.append("TARGET BUILDING")
    parts.append(f"  s_fid:             {n['record_id']}")
    parts.append(f"  municipality:      {n['munic']}")
    if n["lat"] is not None and n["lon"] is not None:
        parts.append(f"  centroid:          lat {n['lat']:.5f}, lon {n['lon']:.5f}")
    else:
        parts.append( "  centroid:          (not available in this record)")
    label = "destroyed" if n["damage_val"] == 1 else "survived"
    parts.append(f"  damage_val:        {n['damage_val']} ({label})")
    parts.append(f"  evidence conf:     {n['conf']}")
    parts.append(
        f"  GSI hazards:       fire={n['fire']}, "
        f"tsunami={n['tsunami']}, slope_failure={n['slope']}"
    )
    parts.append(f"  USGS MMI:          {n['mmi']:.1f}")
    parts.append(f"  primary peril:     {primary_peril}  [computed from hazard flags]")
    parts.append(f"  secondary peril:   {secondary_peril}  [computed from hazard flags]")
    parts.append(f"  next action:       {next_action}  [computed from damage_val]")

    if precedents:
        parts.append("\nRETRIEVED PRECEDENTS (similar buildings from corpus)")
        for p in precedents[:3]:
            p_id = p.get("s_fid") or p.get("id", "?")
            parts.append(
                f"  - s_fid {p_id}: {p.get('label', '?')}, "
                f"similarity {p.get('similarity', 0):.2f}"
            )

    if narrative:
        parts.append(f"\nRULE-BASED NARRATIVE\n  {narrative}")

    parts.append("\nAUDIT METADATA")
    parts.append(f"  audit_reference: {_AUDIT_REFERENCE}")
    parts.append("  damage labels: Vescovo et al. 2025 Noto Peninsula dataset")
    parts.append("                 n=140,208, F1=0.94 against ground survey (CC-BY 4.0)")
    parts.append("                 DOI 10.5281/zenodo.11055711")
    parts.append("  imagery:       GSI post-event orthophoto, 47 cm/pixel, captured 11 Jan 2024")
    parts.append("  hazard zones:  GSI post-event hazard layer")
    parts.append("  shake intensity: USGS ShakeMap")

    return "\n".join(parts)
