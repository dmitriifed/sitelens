# SiteLens Data Layer

This directory contains Layer-0 data fetching and preparation scripts, plus configuration and attribution for external datasets.

## Data Sources

### Building Damage Labels

**Vescovo, R. et al. (2025).** *Noto Peninsula 2024 earthquake building damage assessment.* Zenodo. https://doi.org/10.5281/zenodo.11055711

- **License:** CC-BY 4.0
- **Ground truth source:** n = 140,208 buildings, F1 = 0.94 against ground survey (human-on-foot and expert assessment)
- **Geographic scope:** Noto Peninsula, Japan; 1 January 2024 Magnitude 7.6 earthquake
- **Damage classes:** destroyed (binary baseline); multi-class (fire / seismic / structural) for extended evaluation
- **Attribution requirement:** Any derived dataset, model, or visualization must cite Vescovo et al. 2025 and include the DOI

### Aerial Imagery

**Geospatial Information Authority of Japan (GSI).** Post-event orthophoto tiles, captured 11 January 2024.

- **Source:** GSI tile servers (z=17 and z=18)
- **Resolution:** ~0.47 m/pixel (z=18), ~1.2 m/pixel (z=17)
- **License:** Attribution required for derivatives
- **Attribution requirement:** Must include 「地理院タイル」 (Map tiles by GSI) on any derived imagery

## Hero Zone

**Wajima Asaichi morning market district fire zone**

- **Location:** ~37.4002°N, 136.8950°E, Wajima City, Noto Peninsula
- **Disaster context:** On 1 January 2024, a fire originating in the Asaichi market destroyed approximately 200 stalls across 48,000 m² in ~17 hours. The Noto earthquake of the same day contributed seismic damage to surrounding structures.
- **Dataset signal:** Among 442 destroyed buildings in the demo area, 311 are fire-damaged and 131 are seismic-damaged. This decomposition gives a visually distinctive signal for multi-hazard attribution and anchors the SiteLens demo narrative.
- **Reference:** Same zone featured in the Sensing Risk pitch deck (Slide 7).

## Scripts

### `fetch_gsi_tiles.py`

Fetches GSI orthophoto tiles for a specified bounding box, stitches them into a single georeferenced GeoTIFF, and produces a quick-look PNG for visual verification.

**Status:** Validated, no further work required.

**Inputs:** Bounding box (decimal degrees), zoom level (17 or 18), output directory

**Outputs:**
- Georeferenced GeoTIFF (full resolution)
- Quick-look PNG (downsampled, Web Mercator projection)

**Attribution:** Produces a GeoTIFF with embedded GSI attribution in TIFF tags.

### `regenerate_multihazard.py`

Overlays Vescovo et al. damage polygons on the orthophoto, validates polygon-orthophoto alignment, and produces three visualizations:
- `quicklook_with_polygons.png`, all buildings (destroyed in red, survived in blue)
- `destroyed_only.png`, destroyed buildings only
- `multihazard.png`, destroyed buildings colored by damage class (fire vs seismic)

**Status:** Validated, CRS mismatch handling implemented, no further work required.

**Inputs:** Orthophoto GeoTIFF, polygon GeoPackage (Vescovo et al. format)

**Outputs:** Three PNG visualizations + validation log

### `extract_crops.py`

Extracts per-building crops from the orthophoto at a fixed size (256×256 px) centered on each building polygon, producing the dataset for CNN training.

**Status:** Validated; produced the 1,967-crop training set.

**Inputs:** Orthophoto GeoTIFF, polygon GeoPackage

**Outputs:** crops/ directory with numbered `.png` files + metadata CSV

## Framing Note: F1 Score Honesty

Vescovo et al. report F1 = 0.94 for building damage classification. This is ground-truth accuracy: buildings inspected on foot or by experts working with multiple data sources (aerial, ground survey, historical records).

SiteLens is image-only. The model is trained and evaluated separately against a held-out split of the Vescovo labels; its F1 is lower than 0.94, which is the correct result for image-only classification.

Every audience-facing output (README, demo, papers) reports the two numbers separately:
- Vescovo et al. 2025 ground truth: F1 = 0.94 (human ground survey, n = 140,208).
- SiteLens model: F1 = [measured] (image-only, evaluated against a held-out test split).

## Data Flow

```
GSI tiles (fetch_gsi_tiles.py)
    ↓
Orthophoto GeoTIFF + Vescovo polygons
    ↓
Polygon-orthophoto overlay validation (regenerate_multihazard.py)
    ↓
Per-building crop extraction (extract_crops.py)
    ↓
MobileNetV2 training on 256×256 crops
    ↓
Inference pipeline (bbox in, predictions out)
    ↓
LLM report generation
    ↓
Streamlit app
```

## Reproducibility and Licensing

All code in this project is MIT licensed (see ../LICENSE). All outputs that include Vescovo et al. data or GSI imagery must include the required attributions. Derived datasets should be shared under CC-BY 4.0 to maintain the license chain.

To set up a fresh environment:
```bash
cd ..
pip install -r requirements.txt
```

Then fetch tiles for the hero zone and validate with `regenerate_multihazard.py` as a first reproducibility test.
