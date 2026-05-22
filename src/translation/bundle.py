"""
bundle.py — assemble a record + context into prompt-ready text.

Layer 6 helper. Converts a per-building record from labels.csv plus
optional retrieved precedents and Layer 3 narrative into the user-content
block consumed by the audience translator.
"""

from typing import Optional


_PERIL_PRIORITY = ["fire", "tsunami", "slope_failure"]
_PERIL_FLAGS = {
    "fire":          "gsi_fire",
    "tsunami":       "gsi_tsunami",
    "slope_failure": "gsi_slope_failure",
}


def _compute_next_action(record: dict) -> str:
    """Return the recommended next-action from damage_val alone."""
    return "field inspection" if record["damage_val"] == 1 else "desk approval"


def _compute_perils(record: dict) -> tuple[str, str]:
    """Return (primary_peril, secondary_peril) from hazard flags + damage_val.

    Peril attribution is only meaningful for damaged buildings. For
    survived buildings, return a sentinel that the prompts render
    audience-appropriately ("not applicable", "none documented", etc.).
    """
    if record["damage_val"] == 0:
        return "none (building survived)", "none (building survived)"

    active = [p for p in _PERIL_PRIORITY if record.get(_PERIL_FLAGS[p])]
    if not active:
        return "seismic", "none indicated"
    primary = active[0]
    secondary = active[1] if len(active) > 1 else "none indicated"
    return primary, secondary


def format_bundle(
    record: dict,
    precedents: Optional[list[dict]] = None,
    narrative: Optional[str] = None,
) -> str:
    """Build the user-content block for an audience translation call."""
    parts = []

    primary_peril, secondary_peril = _compute_perils(record)
    next_action = _compute_next_action(record)

    # Target building — the canonical record for this translation
    parts.append("TARGET BUILDING")
    parts.append(f"  s_fid:             {record['s_fid']}")
    parts.append(f"  municipality:      {record['municipality']}")
    parts.append(f"  centroid:          lat {record['centroid_lat']:.5f}, lon {record['centroid_lon']:.5f}")
    label = "destroyed" if record["damage_val"] == 1 else "survived"
    parts.append(f"  damage_val:        {record['damage_val']} ({label})")
    parts.append(f"  evidence conf:     {record['conf']}")
    parts.append(
        f"  GSI hazards:       fire={record['gsi_fire']}, "
        f"tsunami={record['gsi_tsunami']}, "
        f"slope_failure={record['gsi_slope_failure']}"
    )
    parts.append(f"  USGS MMI:          {record['usgs_mmi']:.1f}")
    parts.append(f"  primary peril:     {primary_peril}  [computed from hazard flags]")
    parts.append(f"  secondary peril:   {secondary_peril}  [computed from hazard flags]")
    parts.append(f"  next action:       {next_action}  [computed from damage_val]")

    # Retrieved precedents — Layer 2 output (similar buildings from corpus)
    if precedents:
        parts.append("\nRETRIEVED PRECEDENTS (similar buildings from corpus)")
        for p in precedents[:3]:
            parts.append(
                f"  - s_fid {p['s_fid']}: {p.get('label', '?')}, "
                f"similarity {p.get('similarity', 0):.2f}"
            )

    # Layer 3 narrative if present
    if narrative:
        parts.append(f"\nRULE-BASED NARRATIVE\n  {narrative}")

    # Audit metadata — provenance is part of the input, not an afterthought
    parts.append("\nAUDIT METADATA")
    parts.append("  damage labels: Vescovo et al. 2025 Noto Peninsula dataset")
    parts.append("                 n=140,208, F1=0.94 against ground survey (CC-BY 4.0)")
    parts.append("                 DOI 10.5281/zenodo.11055711")
    parts.append("  imagery:       GSI post-event orthophoto, 47 cm/pixel, captured 11 Jan 2024")
    parts.append("  hazard zones:  GSI post-event hazard layer")
    parts.append("  shake intensity: USGS ShakeMap")

    return "\n".join(parts)
