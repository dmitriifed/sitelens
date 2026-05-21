# SiteLens AI — build log

Last updated: project initialised, sections 1–5 drafted, sections 6–8 scaffolded for week-by-week population.

This document captures every load-bearing decision for the SiteLens AI bootcamp build. It exists so any future working session, code review, or portfolio reference can pick up exactly where we left off without re-debating settled questions. Read in full before starting a new session; treat as authoritative until explicitly revised.

This log is the bootcamp-scoped parallel to the Sensing Risk decisions log. The two are kept separate by design (see Section 1).

---

## 1. Purpose and relationship to Sensing Risk

**SiteLens AI is the software face of the Sensing Risk thesis, scoped to the Developers Institute GenAI & ML bootcamp capstone.** It takes building imagery (post-event aerial orthophoto in the demonstrable case, generalisable to drone stills and street-level photos) and produces structured per-building damage classification plus a generated inspection report. It is software-only.

**The relationship to Sensing Risk.** Sensing Risk is the company. SiteLens is the bootcamp deliverable that demonstrates Layer-1 of the Sensing Risk stack — the imagery-in / structured-output-out pipeline — at a scale and rigour appropriate for a 5-week capstone window. The thesis, the wedge, the dataset, and the framing are inherited from Sensing Risk; the engineering, the model training, and the evaluation are produced inside SiteLens.

**Why two logs, not one.** The Sensing Risk decisions log holds strategic positioning, market framing, design-system discipline, slide-by-slide deck decisions, and cross-cutting policy (e.g. evidence classes, italic discipline, red discipline). None of that belongs in a public bootcamp portfolio. The SiteLens log holds engineering decisions, evaluation discipline, weekly milestones, and demo narrative. The Sensing Risk log stays in the private project space and never enters the public SiteLens repo. The SiteLens log can be committed to the SiteLens repo (which is itself owned by the founder, not the school — see initial setup note below).

**Naming discipline.** SiteLens is the working name for the bootcamp deliverable. It is *not* a Sensing Risk product name. In any Sensing Risk-facing context (deck, outreach, application), the artefact is referenced as "Layer-1 software validation, demonstrated on the Noto 2024 dataset" — not as "SiteLens." Brand boundaries stay clean in both directions: the SiteLens README references Sensing Risk as motivation; Sensing Risk materials never reference SiteLens by name.

**Initial setup note (May 10 2026).** Repository lives on the founder's personal GitHub, under personal credentials, with the school added as collaborator only if and when needed for grading. Default license MIT. This is the standard bootcamp portfolio path and what the curriculum's GitHub Student Pack module assumes.

**Provenance-by-default discipline (May 20 2026).** Every pipeline stage emits (a) a per-run summary JSON capturing inputs, parameters, code version (git commit), and counts; (b) per-record metadata sufficient to trace each output back to its source inputs and the transformation parameters used. Filenames are deterministic from source IDs. Sanity-check displays surface source IDs alongside output. Established at `pipeline/extract_crops.py` (Layer-1 crop extractor): `extraction_summary.json` records the git commit, timestamp, GPKG and raster paths, CRS, all extraction parameters, and the full count chain from polygons-in-extent to crops-written; `labels.csv` carries `s_fid`, centroid coordinates, polygon WKT, and pixel-space window parameters for every crop. The audit layer at the top of the gradient is only as strong as the traceability discipline at every layer beneath it.

---

## 2. Scope discipline

**What SiteLens is.**

A multimodal building damage assessment pipeline that:
- Ingests aerial imagery (GSI orthophoto) for a defined bounding box.
- Runs per-building classification against the Vescovo et al. 2025 ground-truth labels.
- Generates a structured inspection report via a language model.
- Demonstrates the pipeline through an interactive demo (Gradio or notebook).

**What SiteLens is not.**

- Not a hardware product. The Sensing Risk module-first hardware thesis is referenced as motivation in the README; no hardware claims are made by SiteLens itself.
- Not a real-time inference engine. Batch inference is acceptable; the demo can take seconds per building.
- Not a production-grade web service. A local Gradio app or a clean notebook is the deliverable.
- Not a Japanese-localised commercial product. The demonstration runs on Japanese data because that is where the validated ground truth is, but no claims are made about J-PIC schema compliance, MLIT alignment, or inspector-workflow integration. Those belong to Sensing Risk's later phases.
- Not a peer-reviewed research contribution. The evaluation is rigorous and honest, but the deliverable is a portfolio piece, not a paper.

**The scope discipline mirrors the stage-claim discipline already locked in the Sensing Risk decisions log §1.** Hardware sits at "Idea." SiteLens sits at "working software prototype, evaluated against peer-reviewed ground truth, no production claims." Both stage claims must hold under cross-examination.

**What stays out of the SiteLens repo entirely.**

- The Sensing Risk pitch deck, decisions log, application drafts, outreach correspondence.
- Any document that names corporate prospects, partners, or undisclosed collaborators.
- Any internal commentary that would be inappropriate for a public portfolio.

---

## 3. Dataset and existing assets

**Ground truth.** Vescovo, R. et al. (2025). Noto Peninsula 2024 earthquake building damage dataset. n = 140,208 buildings, F1 = 0.94 against ground survey, CC-BY 4.0. Zenodo DOI: 10.5281/zenodo.11055711.

**Imagery.** GSI post-event orthophoto tiles at z=18 (~0.47 m/pixel for the Wajima Asaichi market hero zone, captured 11 January 2024) and z=17 (~1.2 m/pixel for wider Wajima context). Required attribution on any derived imagery: 「地理院タイル」 (Map tiles by GSI).

**Hero zone.** Wajima, Asaichi morning market fire district, ~37.4002°N, 136.8950°E. This is the same zone used in the Sensing Risk pitch deck Slide 7. The fire-vs-seismic decomposition (311 fire / 131 seismic among 442 destroyed buildings) is the visually distinctive signal that anchors the demo narrative.

**Existing code (Layer-0, validated, migrated from Sensing Risk).**

- `data/fetch_gsi_tiles.py` — GSI tile fetcher and stitcher. Already validated against the Wajima bounding box. Produces georeferenced GeoTIFF.
- `data/overlay_damage.py` — overlay validation script. Confirms polygon-orthophoto alignment and produces the `quicklook_with_polygons.png` baseline visualisation. CRS-mismatch handling already implemented.

These two scripts are the project's Layer-0 — already validated, no further work needed before they feed Week 11's crop extraction. Migrated into SiteLens with full attribution headers and dataset citations.

---

## 4. Honest framing of model performance

**The single most important framing decision in this project.** Vescovo et al.'s F1 = 0.94 is *human ground-survey* validation — buildings inspected on foot or by experts working with multiple data sources. It is not image-only model performance. SiteLens is image-only. The model's F1 will be lower, and that is correct.

**The discipline.** In every audience-facing context (README, demo, presentation, LinkedIn post, capstone submission), the two numbers are reported separately and never conflated:

- "Vescovo et al. 2025 ground truth: F1 = 0.94 (human-on-human, ground survey, n = 140,208)."
- "SiteLens model: F1 = [actual measured number] (image-only classification, evaluated against held-out test split of Vescovo labels)."

A target F1 > 0.6 for image-only binary classification (destroyed vs. survived) is a defensible MVP threshold. Better is welcome but not required.

**Why this matters.** A capstone presentation that quotes "F1 = 0.94" as the model's accuracy will be (correctly) read as either dishonest or incompetent by anyone who has worked with the dataset. The same applies to downstream audiences — bootcamp instructors, PhD admissions, future employers. The only durable position is the honest one: this model is rigorously evaluated against the strongest ground truth available for this disaster, and the actual measured number is reported transparently.

**Parallel to Sensing Risk's stage-claim discipline.** The Sensing Risk decisions log §1 holds a rule that strong CV evidence must not pull the hardware claim from "Idea" toward "Design." The same rule applies in reverse here: a strong ground-truth dataset must not pull the model-performance claim toward the ground-truth number. Each claim earns its own evidence.

---

## 5. Bootcamp alignment

**Demo Day:** Sunday 14 June 2026, 09:30–11:30, morning slot.

**Capstone scope submission:** Week 11 Day 2 — Monday 1 June 2026 (public commitment to the build, after which scope is locked).

**Capstone submission:** Week 12 Day 5 — Thursday 11 June 2026.

**Current position (10 May 2026):** start of Week 8. Behind on Weeks 6 (CNN material) and 7 (transformers, BERT, fine-tuning).

**Catch-up strategy: subsume, do not separate.** Week 6 and 7 material is caught up by being used in subsequent weekly projects, not by going back to revisit lectures cold. Specifically:

- Week 7 BERT/embeddings → used in Week 8's vector DB project (foundation for the report-retrieval layer).
- Week 6 CNN training → used in Week 11's capstone classifier.

This means catch-up happens by forward motion, with one short evening review (60–90 min) of the relevant lecture notebook before each dependent week. Two evening reviews total: one this week (Week 7 BERT/embeddings, before the Week 8 vector DB project), one before Week 11 starts (Week 6 CNN training).

**Catch-up status (18 May 2026).**

- *Week 7 BERT / embeddings:* paid down implicitly through the Week 8 hackathon. Sentence-transformers, vector DB, and RAG are now operational knowledge rather than lecture material. No formal revisit needed.
- *Week 6 CNN training:* banked evening of 18 May 2026. Anchored against the bootcamp's cats-vs-dogs notebook roadmap as a direct Week 11 capstone template. Concepts covered: convolution and parameter sharing, pooling and translational invariance, ReLU and output activations (sigmoid vs softmax), binary cross-entropy + Adam, overfitting diagnostics, dropout + data augmentation + L2 regularization, class imbalance handling. Transfer learning (MobileNetV2 / ResNet50) deferred to Wed 20 May 2026 for hands-on resolution once crops are loadable.

Both evening reviews from the original catch-up commitment are now complete. Forward motion is unblocked.

**Week-to-deliverable mapping.**

| Week | Dates (Sun–Thu) | Bootcamp topic | SiteLens project deliverable |
|---|---|---|---|
| 8  | May 10–14 | NLP, vector databases, RAG | Inspection-precedent retrieval prototype (Pinecone + sentence-transformers) |
| 9  | May 17–21 | Prompt engineering, open-source LLMs | Inspection report generator: structured record → narrative report |
| 10 | May 24–28 | Agentic AI, MCP | Optional thin agent (bbox in → report out). Held loosely; consolidation/recovery time if 8–9 ran hot. |
| 11 | May 31–Jun 4 | Capstone build (scope due Mon Jun 1) | CV classifier on Noto crops + scene-level pipeline + per-class F1 evaluation |
| 12 | Jun 7–11 | Capstone build (submit Thu Jun 11) | Gradio demo + README + presentation deck |
| 13 | Jun 14 | Demo Day (Sun morning) | Present |

**Workweek discipline.** Israeli Sunday-to-Thursday workweek. Mornings: bootcamp lectures (exploratory learning). Afternoons: SiteLens building (project synthesis). Friday–Saturday: weekend, protected for rest by default. As deadlines approach (especially Weeks 11–12), some weekend work is acceptable but not expected as baseline.

**This week (Week 8, May 10–14): calm and steady.** Foundation week. Sunday: setup (repo, build log, README, file migration). Monday–Thursday: vector DB project, with one evening review of last week's BERT material. No crunch. Confidence and process induced before later weeks accelerate.

---

## 6. Architecture and weekly module decisions

*Populated as we build, week by week. Each weekly project entry captures: what was built, what was deliberately not built, what was learned, what carries to the next week.*

### Week 8 (May 10–14): vector DB / retrieval

**Built:** schema reference (`01_vescovo_schema.ipynb`), end-to-end RAG hello-world (`02_hello_world_rag.ipynb`), RAG + summarisation prototype (`03_summarisation.ipynb`). Sample data committed: 18 Wajima Asaichi fire-zone records (`data/samples/sample_records.json`, 12 destroyed / 6 survived).

**Stack:** `sentence-transformers/all-MiniLM-L6-v2` for embeddings (pre-trained, general-domain, kept as-is); Pinecone serverless for vector store; rule-based template parser + narrative generator for summarisation (NOT abstractive ML — see below).

**Architectural decision — the layered gradient (load-bearing insight of Week 8).**

The system is a layered pipeline where structure increases up the chain of command. Each tool sits in its appropriate layer; structure is not forced on lower layers where messy reality belongs.

- *Raw layer:* free-form inspector input. Messy, partial, possibly contradictory. Preserved unprocessed.
- *Retrieval layer:* sentence-transformer similarity surfaces precedent records. Semi-structured. Ranked but unaggregated. Raw records remain visible with similarity scores.
- *Narrative layer:* rule-based aggregation across the retrieved set. Deterministic, grounded, audit-ready (`parse_hits` + `narrative_sentence`).
- *Audit layer:* timestamped, attributable, version-stamped. Highest structure. Currently implicit in Pinecone metadata; will become explicit in Streamlit display.

Each layer is visible to the layer above. Field decision-maker sees raw + retrieval; senior coordinator sees narrative + audit. Nothing hidden from the floor; nothing unprocessed reaches the senior office. The structural gradient mirrors the Sensing Risk chain-of-command reduction thesis (Sensing Risk decisions log §1) — this is the empowerment thesis in product architecture.

**Rejected at the narrative layer:** t5-small as abstractive summariser. Tested 13 May 2026 on top-3 retrieved records. Output:

> *"Summary: evidence: multi-source assessment. Building destroyed. Hazard: fire. MMI 8.4 (severe shaking). evidence: multi-source assessment. evidence: multi-source assessment."*

Regurgitation with repeated phrases and no aggregation. Diagnosis: general-domain abstractive models on already-templated input have nothing to compress; they re-emit chunks. Not specific to t5-small — BART or Pegasus would fail similarly. ML summarisation belongs *above* or *below* the narrative layer (consuming the rule-based narrative + raw records, or parsing free-form input into structured fields), not *at* it.

**Implemented at Layer 5 (added 14 May 2026 — corrects the "out of hackathon scope" framing in earlier rigidity-map):** `sshleifer/distilbart-cnn-12-6` as the senior-coordinator cross-summary. Input: inspector free-form text + rule-based narrative + retrieved record texts, assembled into a single paragraph. The free-form input gives the model real material to compress (unlike Layer 3's all-templated input). Output is more extractive than deeply abstractive — the model concatenates and lightly reorders rather than synthesising — but it produces coherent, grounded text without the regurgitation pattern that disqualified t5 at Layer 3. This validates the architectural placement: ML summarisation belongs *above* the narrative layer, not *at* it.

**Tutor feedback (14 May 2026):** project described as "very original"; minimal questioning. Specific question raised: how building coordinates are obtained (answered: centroids derived from GPKG geometry at sample-generation time). Suggested extension: prompt engineering for cross-context application — maps directly onto Week 9 work and the unloosened rigidity faces.

**Deployed:** Streamlit Community Cloud at https://sitelens.streamlit.app/. Layout: dual-pane with sticky map and independently-scrolling notes column, GSI seamlessphoto basemap, deck-red palette (#A41E1E for destroyed, deliberate continuity with Slide 7 and the deck's operational-red discipline). Print-to-PDF rules stack the columns vertically. Repository: github.com/dmitriifed/sitelens, MIT license.

**Four faces of rigidity** (Week 11+ map, not today):
- *Input rigidity* — parser assumes exact template format. Loosens with a learned parser or LLM-based field extraction.
- *Coverage rigidity* — only four template fields. Loosens cheaply by extending the template (footprint, centroid, adjacent-damage context).
- *Output rigidity* — finite if/elif tree. Loosens with fine-tuned generation (capstone fine-tuning question).
- *Domain rigidity* — Vescovo schema only. Loosens highest-leverage by ingesting free-form documents (Vescovo paper PDF, MLIT damage manuals).

### Week 9 (May 17–21): prompt engineering / multi-audience translation

**Pre-work — Layer 1 crop extractor (18 May 2026).** Built `pipeline/extract_crops.py`. Layer 1 data preparation for the Week 11 capstone. Walks the Vescovo GPKG, crops each building polygon from the GSI Wajima orthophoto, writes per-building PNG plus a labels CSV in `flow_from_dataframe` shape. 2,045 valid crops extracted from 2,084 polygons in raster extent. 37 + 2 ambiguous labels dropped (damage_val 9 obstructed and 99 inconsistent per schema).

**Concepts applied:**

- *Geo stack and CRS alignment.* GeoPandas (vector) + Rasterio (raster) with explicit CRS assertion before any geometry math. Both files are EPSG:4326 so the assertion passes; the discipline of asserting is more important than the specific result.
- *Spatial filter pushed to the file driver.* `bbox=` argument on `read_file()` — no Python loop over 140k polygons just to discard most.
- *World ↔ pixel conversion via `from_bounds()`.* Rasterio's `windows` module converts world bbox to pixel window using the raster's affine transform.
- *Context padding.* 25% of larger side around each polygon. Buildings need context (neighbours, debris field, street) for damage classification; tight crops lose signal.
- *Squarify in pixel space, not world space.* Load-bearing engineering finding. At Wajima (≈37.4°N), `transform.a` (longitude degrees per pixel) is ≈1.26× larger than `transform.e` (latitude degrees per pixel) because the GSI orthophoto preserves ground distance, not degree size. Squarifying in world coordinates therefore produces a 0.80:1 pixel rectangle, squashing horizontal features by ≈20% before resize. Fix: compute the unsquared pixel window with `from_bounds()`, then extend the shorter pixel dimension to match the longer. Output is genuinely square in pixels and represents genuinely square ground area.
- *Edge-fill / low-variance filtering.* `boundless=True` returns black-filled pixels for polygons at the raster edge; some polygons near the coast capture mostly water. Filter at extract time: skip crops where >20% of pixels are exactly zero OR overall pixel std < 10. Skipped crops logged separately to `extraction_skipped.csv` so the audit record is preserved rather than silently dropped.
- *MMI as carried-but-not-used.* `USGS_MMI = 8.4` is constant across all Wajima buildings (ShakeMap pixel coarser than raster extent). Column retained in `labels.csv` despite zero predictive variance in this dataset because (a) it varies once the dataset extends beyond Wajima, (b) it varies across multi-event futures (Kumamoto, Tohoku), (c) the CNN takes images only so the column does not affect training, (d) re-extracting later costs more than carrying it now.

**Provenance discipline applied to Layer 1.** Per the new §1 entry in the Sensing Risk decisions log, the extractor emits:
- `labels.csv` with per-crop provenance: `s_fid`, filepath, centroid lon/lat, polygon WKT, pixel window (col_off, row_off, width, height), all source metadata (municipality, hazard flags, MMI, conf).
- `extraction_summary.json` with per-run provenance: run timestamp UTC, git commit, input paths and CRS, parameters used (TARGET_SIZE, CONTEXT_PAD, resampling, squarify_mode), counts (polygons in extent, dropped per reason, skipped per reason, crops written), class balance.
- Filenames `bldg_<s_fid:06d>.png` deterministic from source ID.
- Sanity-grid titles surface `s_fid` and centroid lon/lat so any visually-suspicious crop is one CSV lookup away from its source polygon.

**Sanity-check outcomes.** Stratified 6-destroyed + 6-survived grid confirms label-image consistency. Destroyed crops show debris fields and fragmented rooflines; survived crops show intact rectangular roofs. One edge-fill / coastal water crop visible in the pre-filter grid; the variance filter eliminates these on re-run.

**Open for Wednesday 20 May 2026:**
- Transfer learning vs train-from-scratch architecture decision. Recommend transfer learning (MobileNetV2 pretrained, frozen base, retrained head) on empirical grounds — small dataset typically favours it.
- Class imbalance ratio in Wajima crops (destroyed:survived) — confirm after current run, decide between class weights at training time vs stratified subsampling at extract time.

**Audience-translation build (Tue–Thu 19–21 May 2026).** [Placeholder — to be populated as the build proceeds. Maps directly onto SR decisions log §4 voice-localisation extension: same canonical record, multiple downstream audience registers. Target three audiences first — insurance adjuster, structural engineer, legal counsel — as the moat-spanning stress test.]

---

## 7. Evaluation discipline

**Pre-Week-11 commitments (18 May 2026):**

- *Report per-class F1, precision, recall, and confusion matrix — not accuracy.* The class imbalance in Vescovo (destroyed is a small minority of 140,208 buildings) makes accuracy uninformative. A model with 95% accuracy that catches 30% of destroyed buildings is useless for triage; a model with 80% accuracy that catches 90% of destroyed buildings is the product. Per-class metrics are the only honest report.

- *Track model F1 and Vescovo human-on-human F1 separately.* The §4 honest-framing discipline applies: every published number includes both, never conflated. Expected model F1 in the 0.6–0.75 range for image-only binary classification at 64×64; that is a defensible result and the honest one. Quoting Vescovo's 0.94 as the model number is the single most damaging move available.

- *AUC as a complementary monitoring metric during training.* AUC is threshold-independent and more honest than accuracy on imbalanced data. Default monitoring set: training loss, validation loss, validation AUC, validation per-class F1.

*The full evaluation harness — confusion matrix visualisation, train/val/test split discipline, held-out test set protection, baseline-vs-model comparison framing — locks in Week 11 against the actual capstone model.*

---

## 8. Demo narrative

Six-beat structure inherited from the Sensing Risk demo video concept (Sensing Risk decisions log §11, post-submission asset). Evolves as the build evolves; final draft in Week 12 against the actual demo state.

**Week 8 / hackathon demo (Day 3 deliverable):**

1. *The problem* — inspector at a damaged building, senior staff in office, decision asymmetry.
2. *Free-form input* — inspector describes what they see in plain English.
3. *Retrieval* — similar past records surface with similarity scores. Raw, ranked, unaggregated.
4. *Narrative* — rule-based aggregation produces a structured field assessment.
5. *Audit* — timestamped, attributable, model-versioned record for the senior coordinator.
6. *What's next* — four rigidity faces, how they loosen toward Week 11.

The four layers are visible on one Streamlit page. The viewer's eye moves down through the structural gradient — that's the demo.

---

## 9. Repository structure

Updated May 11 2026 to reflect Week 8 refactor.

```
sitelens/
├── README.md
├── LICENSE
├── .gitignore
├── sitelens_build_log.md           (this file)
├── .env                            (gitignored — PINECONE_API_KEY etc.)
├── data/
│   ├── README.md                   (data attribution: Vescovo et al., GSI)
│   ├── raw/                        (gitignored — full GPKG, GSI tiles)
│   ├── processed/                  (gitignored — embeddings cache, generated text)
│   ├── samples/                    (committed — 20-record JSON for hello-world & tests)
│   │   ├── generate_samples.py     (run once to produce sample_records.json)
│   │   └── sample_records.json     (committed after generation)
│   └── crop_extractor.py           (Week 11 deliverable)
├── notebooks/
│   ├── 01_vescovo_schema.ipynb     (schema reference, value distributions)
│   ├── 02_hello_world_rag.ipynb    (Week 8 — Pinecone + sentence-transformers)
│   ├── week09_report_gen.ipynb     (Week 9 deliverable)
│   ├── week10_agent.ipynb          (Week 10 — optional)
│   └── week11_classifier.ipynb     (Week 11 deliverable)
├── src/
│   ├── data/
│   │   ├── load_vescovo.py         (GPKG loading, spatial filters)
│   │   └── records_to_text.py      (row_to_text, gdf_to_records)
│   ├── embedding/
│   │   └── embed_records.py        (sentence-transformer wrapper, lazy-load)
│   └── retrieval/
│       └── pinecone_client.py      (connect, upsert, query helpers)
├── model/
│   ├── train.py                    (Week 11 deliverable)
│   ├── evaluate.py                 (Week 11 deliverable)
│   └── weights/                    (gitignored except placeholder)
├── pipeline/
│   ├── fetch_gsi_tiles.py          (Layer-0 — GSI tile fetcher, validated)
│   ├── regenerate_multihazard.py   (Layer-0 — polygon overlay + multihazard vis, validated)
│   └── run_inference.py            (Week 11–12 deliverable)
├── report/
│   ├── generator.py                (Week 9 deliverable)
│   └── prompts/
└── app/
    └── gradio_demo.py              (Week 12 deliverable)
```

**Run all pipeline scripts from the project root (`sitelens/`).** Relative paths in scripts resolve against CWD.

---

## 10. Open questions

- Bootcamp T&Cs reviewed for IP language (verification step from initial setup discussion). Quick read of enrolment agreement; search for "intellectual property," "ownership," "deliverables."
- Pinecone free tier quota — confirm sufficient for Week 8 + Week 9 demos.
- LLM choice for Week 9 report generator — Gemini 1.5 Flash (free tier), OpenAI API, or local Mistral-7B. Decision deferred to start of Week 9 based on bootcamp-provided credits and time budget.
- Whether to migrate the multihazard rendering script from Sensing Risk into SiteLens or keep it Sensing Risk-only. Lean: keep it Sensing Risk-only; SiteLens produces its own predicted-vs-ground-truth visualisations.
- License: MIT confirmed as default. Switch only if a specific reason emerges.
- Repo public from day one, or private until demo day? Default: private until Week 12, public for Demo Day. Easy to flip.
- Multi-input senior summary (surfaced 14 May 2026 — Week 9 candidate). Layer 5's coordinator role is inherently cross-assessment; the current single-input version technically works but doesn't demonstrate the senior-coordinator value proposition. Implementation needs: session-state queue of assessments, "add to summary" UI control, list-aware Layer 5 input construction, prompt scaffolding so distilbart treats the input as multiple discrete assessments rather than one long stream (real concern at 1024-token input limit). Pairs naturally with Week 9 prompt-engineering theme. 2–4 hours of focused work.

- Field Assessment caption redundancy (fixed 14 May 2026). The narrative + stats line repeated the same information. Replaced stats line with assessment metadata — retrieved-precedent count, average similarity score, audit signal ("rule-based aggregation, no ML at this layer"). Layer 5 caption mirrors with inverse signal ("abstractive synthesis, may rephrase but does not invent facts"). Architecture surfaces in one line per layer.

- Project virtual environment switch (May 2026). Migrated from global Python env to `.venv` in repo, curated `requirements.txt` reflecting actual deployed dependencies (drops stale `pinecone-client` for `pinecone`, removes commented-out future-week placeholders). Prerequisite for predictable Streamlit Cloud deploys and Week 11 CV dependency isolation.

- Evidence-class axis (surfaced 13 May 2026, hackathon Day 1). The layered gradient (raw → retrieval → narrative → audit) is the *structural* axis. There is an orthogonal *epistemic* axis the system does not yet track: each datum is one of *conclusive/definitive* (e.g. Vescovo damage label, peer-reviewed measurement), *cross-referential/supportive* (e.g. similarity score, hazard-zone overlay, multi-source agreement), or *subjective/personified* (e.g. inspector field note, witness statement). Both axes matter independently. A definitive record at the raw layer is treated differently from a subjective record at the audit layer; the current system collapses the second axis. For Week 11+: data model should carry an `evidence_class` field; UI should surface class (colour, label, qualifier). Parallel to consular/legal/intelligence systems (documents vs cross-references vs interview); deck's Slide C has a related but distinct framework (citation-strength classes A–D for external sources). Worth a structured exploration before Week 11 capstone scope is locked.

**Closures (18 May 2026):**

- *LLM choice for Week 9 report generator — closed.* Distilbart-cnn-12-6 retained at Layer 5 (generalist cross-summary, local, deterministic, demo-day robust). Candidate Gemini 1.5 Flash to be A/B tested Wed 20 May 2026 at the new audience-translation layer (Layer 6), where audience-specific semantic understanding matters more than reproducibility. Likely outcome: split-stack — local model at Layer 5 for cross-summary, remote model at Layer 6 for audience translation, with a Demo-Day graceful-degradation fallback if remote quota or network fails.

- *Multi-input senior summary — closed, reframed.* Subsumed into the audience-translation build as one audience among many (the senior coordinator is one of the seven downstream audiences identified in the Sensing Risk decisions log §4 voice-localisation extension). The feature is delivered as a special case of the general translation pattern: same prompt scaffolding, longer input bundle (5–10 assessments rather than one). No separate UI plumbing.

**New open question (18 May 2026):**

- *Transfer learning vs train-from-scratch for the Week 11 capstone classifier.* Decision deferred to Wed 20 May 2026 once first crops are loadable and a baseline can be run. Default recommendation: transfer learning (MobileNetV2 pretrained on ImageNet, frozen base, retrained Dense + Dropout + Sigmoid head on Noto crops). Decision criteria: (a) per-class F1 on a small validation split with 10 epochs of each approach, (b) training time per epoch, (c) ease of explanation in the capstone presentation. Pragmatic instinct: transfer learning wins on small datasets, but train-from-scratch may produce a more interpretable story for the bootcamp evaluator.

---

End of build log v0.
