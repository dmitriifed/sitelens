"""Convert Vescovo GeoDataFrame rows to natural-language strings for embedding."""

import pandas as pd

MMI_LABELS = [
    (9, "violent"), (8, "severe"), (7, "very strong"),
    (6, "strong"), (4, "moderate"), (0, "light"),
]

DAMAGE_TEXT = {
    0: "survived",
    1: "destroyed",
    9: "obstructed",
    99: "inconsistent footprint",
}


def mmi_label(mmi: float) -> str:
    for threshold, label in MMI_LABELS:
        if mmi >= threshold:
            return label
    return "light"


def row_to_text(row) -> str:
    outcome = DAMAGE_TEXT.get(row.damage_val, "unknown")
    hazards = [
        h for h, flag in [
            ("fire", row.GSI_fire),
            ("tsunami", row.GSI_tsunami),
            ("slope failure", row.GSI_slope_failure),
        ]
        if flag == 1
    ]
    haz_str = ", ".join(hazards) if hazards else "seismic only"
    mmi_str = f"MMI {row.USGS_MMI:.1f} ({mmi_label(row.USGS_MMI)} shaking)"
    loc = row.municipality if pd.notna(row.municipality) else "unknown municipality"
    return (
        f"Building {outcome}. Hazard: {haz_str}. {mmi_str}. "
        f"Location: {loc}. Evidence: {row.conf}-source assessment."
    )


def gdf_to_records(gdf, id_prefix: str = "bldg") -> list[dict]:
    """Convert a GeoDataFrame to a list of {id, text} dicts ready for embedding."""
    return [
        {"id": f"{id_prefix}_{i:04d}", "text": row_to_text(row)}
        for i, (_, row) in enumerate(gdf.iterrows())
    ]
