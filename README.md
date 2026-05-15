# SiteLens AI — Building Damage Assessment Copilot

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://sitelens.streamlit.app/)

![Wajima Asaichi multihazard attribution — Vescovo damage labels over GSI orthophoto](docs/wajima_mini_multihazard_v2.png)

*Wajima Asaichi district, 11 Jan 2024. 442 destroyed buildings classified by hazard mechanism: 311 fire (red), 131 seismic-only (orange), against 1,603 survivors. Imagery: GSI 47 cm/pixel orthophoto. Damage labels: Vescovo et al. 2025 (CC-BY 4.0, F1=0.94 against ground survey).*


> A multimodal building damage assessment pipeline: classifies per-building damage from aerial imagery using a CV model evaluated against peer-reviewed ground-truth labels from the 2024 Noto earthquake, and generates structured inspection reports using a language model.

**Status:** Capstone project in active development. Developers Institute GenAI & Machine Learning Bootcamp, 2026 cohort. Target completion: 14 June 2026.

---

## What this project does

Given a bounding box over a damaged area, SiteLens AI:

1. Fetches post-event aerial orthophoto imagery for the area.
2. Classifies per-building damage (destroyed vs. survived; multi-class extension planned) against ground-truth polygons.
3. Generates a structured inspection report describing damage at building and zone level.
4. Presents the result via an interactive demo.

The demonstration target is the Wajima Asaichi morning market district. On 1 January 2024, the Noto Peninsula earthquake triggered a fire in this district that destroyed approximately 200 stalls across 48,000 m². The dataset distinguishes 311 fire-damage and 131 seismic-damage buildings among 442 destroyed structures, providing a strong test case for multi-cause attribution.

## Status

- [x] Layer-0: GSI orthophoto fetcher (`data/fetch_gsi_tiles.py`)
- [x] Layer-0: Polygon-orthophoto overlay validation (`data/overlay_damage.py`)
- [x] Layer-2: Semantic retrieval (Pinecone + sentence-transformers)
- [x] Layer-3: Rule-based field assessment narrative
- [x] Layer-5: Abstractive cross-summary (distilbart-cnn-12-6)
- [x] Interactive demo (Streamlit) — https://sitelens.streamlit.app/
- [ ] Layer-1: Per-building crop extractor
- [ ] Layer-1: Baseline CNN damage classifier
- [ ] Layer-1: Per-building evaluation pipeline

## Dataset and attribution

This project uses two open datasets, both with full attribution preserved in derived outputs:

**Building damage labels.** Vescovo, R. et al. (2025). *Noto Peninsula 2024 earthquake building damage assessment.* Zenodo. https://doi.org/10.5281/zenodo.11055711. Licensed CC-BY 4.0. n = 140,208 buildings, F1 = 0.94 against ground survey.

**Aerial imagery.** Geospatial Information Authority of Japan (GSI). Post-event orthophoto tiles, captured 11 January 2024, ~0.47 m/pixel at zoom 18. Required attribution on derivatives: 「地理院タイル」 (Map tiles by GSI).

**Important framing note.** The F1 = 0.94 reported by Vescovo et al. is human ground-survey validation, not image-only model performance. The SiteLens model is image-only; it reports its own measured F1 separately, evaluated against a held-out test split of the Vescovo labels. The two numbers are not interchangeable.

## Repository structure

```
sitelens/
├── README.md                   (this file)
├── LICENSE
├── sitelens_build_log.md       (project decisions log)
├── data/                       (data fetching and preparation)
├── notebooks/                  (weekly exploratory work)
├── model/                      (training and evaluation)
├── pipeline/                   (end-to-end inference)
├── report/                     (LLM report generation)
└── app/                        (Streamlit demo)
```

## Context

SiteLens AI is the bootcamp-scoped software face of Sensing Risk, an early-stage venture building inspection-decision infrastructure for damaged building stock. SiteLens demonstrates the imagery-in / structured-output-out pipeline at a scale appropriate for a 5-week capstone window. Hardware, schema localisation, and commercial deployment are out of scope for this project.

## Author

Dmitrii Fedorov — computational architect transitioning to ML/CV/robotics for the built environment.

## License

MIT (see LICENSE).
