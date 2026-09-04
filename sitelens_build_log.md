# SiteLens AI — build log

Last updated: Week 10 simplification pass moves 1–3 landed Mon 25 May 2026 — all three audience harnesses at 100% pass, legal T=0.0 bit-identical confirmed, move-1 fabrication mode corrected; §10 closures updated. 25 May 2026.

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
- Demonstrates the pipeline through an interactive Streamlit demo.

**What SiteLens is not.**

- Not a hardware product. The Sensing Risk module-first hardware thesis is referenced as motivation in the README; no hardware claims are made by SiteLens itself.
- Not a real-time inference engine. Batch inference is acceptable; the demo can take seconds per building.
- Not a production-grade web service. The Streamlit demo is the deliverable; it runs on Streamlit Community Cloud.
- Not a Japanese-localised commercial product. The demonstration runs on Japanese data because that is where the validated ground truth is, but no claims are made about J-PIC schema compliance, MLIT alignment, or inspector-workflow integration. Those belong to Sensing Risk's later phases.
- Not a peer-reviewed research contribution. The evaluation is rigorous and honest, but the deliverable is a portfolio piece, not a paper.

**The scope discipline mirrors the stage-claim discipline already locked in the Sensing Risk decisions log §1.** Hardware sits at "Idea." SiteLens sits at "working software prototype, evaluated against peer-reviewed ground truth, no production claims." Both stage claims must hold under cross-examination.

**What stays out of the SiteLens repo entirely.**

- The Sensing Risk pitch deck, decisions log, application drafts, outreach correspondence.
- Any document that names corporate prospects, partners, or undisclosed collaborators.
- Any internal commentary that would be inappropriate for a public portfolio.

---

## 3. Dataset and existing assets

**Ground truth.** Vescovo, R. et al. (2025). Noto Peninsula 2024 earthquake building damage dataset. n = 140,208 buildings, CC-BY 4.0. Published as Earth System Science Data 17, 5259 (2025); Zenodo DOI: 10.5281/zenodo.11055711. The reported F1 = 0.94 is agreement between the authors' multi-source visual assessment and independent ground-survey photographs, measured on an independently surveyed validation subset — roughly 40 m corridors around documented survey paths in four settlements plus scattered rural areas — not across all 140,208 buildings.

**Imagery.** GSI post-event orthophoto tiles at z=18 (~0.47 m/pixel for the Wajima Asaichi market hero zone, captured 11 January 2024) and z=17 (~1.2 m/pixel for wider Wajima context). Required attribution on any derived imagery: 「地理院タイル」 (Map tiles by GSI).

**Hero zone.** Wajima, Asaichi morning market fire district, ~37.4002°N, 136.8950°E. This is the same zone used in the Sensing Risk pitch deck Slide 7. The fire-vs-seismic decomposition (311 fire / 131 seismic among 442 destroyed buildings) is the visually distinctive signal that anchors the demo narrative.

**Existing code (Layer-0, validated, migrated from Sensing Risk).**

- `data/fetch_gsi_tiles.py` — GSI tile fetcher and stitcher. Already validated against the Wajima bounding box. Produces georeferenced GeoTIFF.
- `data/overlay_damage.py` — overlay validation script. Confirms polygon-orthophoto alignment and produces the `quicklook_with_polygons.png` baseline visualisation. CRS-mismatch handling already implemented.

These two scripts are the project's Layer-0 — already validated, no further work needed before they feed Week 11's crop extraction. Migrated into SiteLens with full attribution headers and dataset citations.

---

## 4. Honest framing of model performance

**The single most important framing decision in this project.** Vescovo et al.'s F1 = 0.94 is *label validation* — agreement between the authors' multi-source visual assessment and independent ground-survey photographs, measured on an independently surveyed subset, not across the full dataset (n = 140,208). The labels themselves are expert image interpretation; the 0.94 is how well that interpretation held up against photographs taken on the ground. It is not image-only model performance. SiteLens is image-only. The model's F1 will be lower, and that is correct.

**The discipline.** In every audience-facing context (README, demo, presentation, LinkedIn post, capstone submission), the two numbers are reported separately and never conflated:

- "Vescovo et al. 2025 ground truth: F1 = 0.94 on an independently surveyed validation subset; dataset n = 140,208."
- "SiteLens model: F1 = [actual measured number] (image-only classification, evaluated against held-out test split of Vescovo labels)."

A target F1 > 0.6 for image-only binary classification (destroyed vs. survived) is a defensible MVP threshold. Better is welcome but not required.

**Why this matters.** A capstone presentation that quotes "F1 = 0.94" as the model's accuracy will be (correctly) read as either dishonest or incompetent by anyone who has worked with the dataset. The same applies to downstream audiences — bootcamp instructors, PhD admissions, future employers. The only durable position is the honest one: this model is rigorously evaluated against the strongest ground truth available for this disaster, and the actual measured number is reported transparently.

**Parallel to Sensing Risk's stage-claim discipline.** The Sensing Risk decisions log §1 holds a rule that strong CV evidence must not pull the hardware claim from "Idea" toward "Design." The same rule applies in reverse here: a strong ground-truth dataset must not pull the model-performance claim toward the ground-truth number. Each claim earns its own evidence.

---

## 5. Bootcamp alignment

**Demo Day:** Thursday 11 June 2026 (actual presented date; the scheduled Sunday 14 June was superseded), 09:30–11:30, morning slot.

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
| 10 | May 24–28 | Agentic AI, MCP | Thin agent (bbox in → report out) + Streamlit audience dropdown + CV warm-up baseline on Wajima crops |
| 11 | May 31–Jun 4 | Capstone build (scope due Mon Jun 1) | CV classifier on Noto crops + scene-level pipeline + per-class F1 evaluation |
| 12 | Jun 7–11 | Capstone build (submit Thu Jun 11) | README + presentation deck |
| 13 | Jun 11 | Demo Day (Thu, same day as submission) | Present |

**Week 10 plan, sharpened (19 May 2026).**

- *Sun–Mon 24–25 May 2026:* thin agent — bbox-in → report-out wrapper over the existing audience translator, Streamlit audience dropdown, multi-record case (senior-coordinator audience as one of many per the SR §4 voice-localisation extension). Half day total. Delivers Week 10's curriculum requirement (agentic AI / MCP) without expanding scope.
- *Tue–Thu 26–28 May 2026:* CV warm-up against the 2,045 Wajima crops. Load `labels.csv` into a `flow_from_dataframe` generator. Define the small CNN from the cats-vs-dogs template at 64×64. Run 5 epochs from scratch and 5 epochs with MobileNetV2 transfer learning. Plot per-class F1, training-vs-validation loss, AUC. Goal: a baseline number in hand before Week 11 starts, so the capstone build is iteration not from-zero.

The original Week 10 framing as "held loosely / consolidation/recovery time if 8–9 ran hot" no longer holds — both halves of the week are now productive. The thin agent is genuinely thin because the audience translator does the heavy lifting.

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

**Audience-translation build (19 May 2026).** Built `src/translation/` package: `bundle.py` (input formatter + deterministic pre-computation of peril attribution and next-action), `prompts.py` (three system instructions + temperature config for insurance / engineering / legal), `audience_translator.py` (Gemini 2.5 Flash call site returning a provenance dict). Notebook `notebooks/week09_report_gen.ipynb` with three audience output cells and three sanity grids across three test records (fire-zone destroyed, seismic-only destroyed, survived).

**LLM choice — resolved to Gemini 2.5 Flash via the new `google.genai` SDK.** The newer SDK with `genai.Client()` is the actively maintained path; the older `google.generativeai` package is legacy. Gemini 2.5 Flash chosen over 1.5 Flash for better instruction-following at similar latency. Free-tier rate limit (~10 RPM) is the operational constraint; the sanity-grid notebook design caches results to stay within budget.

**Architectural decision — guardrail accumulation discipline.** Load-bearing finding from the day. World-knowledge override emerged at the secondary-peril field: the model output "seismic" for fire-zone records because it knows the Noto 2024 event was an earthquake, regardless of constraint language asking it not to derive perils. Adding more constraint language would have masked the symptom. The fix moved peril attribution and next-action into `bundle.py` as deterministic functions; the LLM receives them as pre-computed facts in the input bundle. Its scope is register translation only.

This split — rule-based logic at Layer 3 (deterministic), LLM at Layer 6 (register) — is now the discipline. Captured as a Sensing Risk principle in the decisions log §1 ("Guardrail accumulation as maintenance liability").

**Bug surfaced and patched — peril attribution for survived buildings.** `_compute_perils` originally defaulted to "seismic" when no hazard flags were set, regardless of damage_val. For survived buildings, this produced internally contradictory output ("Damage classification: 損害なし; Primary peril: seismic"). Fixed by adding `damage_val == 0` short-circuit returning a "none (building survived)" sentinel, with one-line prompt updates per audience to render the sentinel in the audience's register. Documented as part of the broader principle: peril attribution is only meaningful for damaged buildings; the pipeline must encode this rather than relying on the model to infer it.

**Status.** Insurance audience validated against a five-criterion sanity grid (J-PIC category, primary peril, secondary peril, evidence basis, next-action). Engineering and legal audiences drafted, sanity grids produce extracted-value tables, full pass/fail evaluation lock-in deferred to Wed 20 May 2026.

**Open for Wednesday 20 May 2026.**
- Build expected-value-vs-actual pass/fail harness for all three audiences. Legal at temperature 0.0 becomes a regression test for model-version drift.
- Validate engineering and legal sanity grids at 100% pass on the three test records, or document specifically which criterion fails on which record.
- LLM A/B test deferred or skipped given Gemini 2.5 Flash is working — re-open only if a specific failure mode surfaces that requires a different model.

**Open for Streamlit integration (deferred to Week 10).**
- Wire Layer 2 (Pinecone precedent retrieval) and Layer 3 (rule-based narrative) into the bundle. Currently `translate()` accepts `precedents` and `narrative` as optional arguments but the notebook does not pass them. The full bundle (precedents + narrative + audit metadata + computed perils) is what makes the translation read as senior-grade rather than single-record.
- Add audience dropdown + "Generate report" button to the existing Streamlit demo at sitelens.streamlit.app.

**Carries forward.** The deterministic-vs-register split now applies to every future Layer 6 call. The notebook's pass/fail harness pattern becomes the evaluation template for Week 11's CV classifier output and Week 12's demo deliverable.

**Class-deck audit findings (22 May 2026).** Audit of the Week 9 implementation against the Developers Institute Week 16 prompt-engineering class deck (David / Developers Institute, "Engineering Predictable AI," May 2026, 33 slides).

*Aligned with class guidance.* Three-role split (System / User / Assistant) used correctly in `audience_translator.py` via `system_instruction` and `contents`. Temperature discipline matches "0 for code, slightly higher for human-read" — 0.0 legal, 0.2 insurance, 0.3 engineering. Structural grounding via "every fact in your output must be supported by the input data" enforced as a constraint, not as tone language. Source provision via the bundle formatter is complete: target record, retrieved precedents, Layer 3 narrative, audit metadata.

*Real gaps identified.*

- *No few-shot examples in any prompt.* All three audiences run zero-shot. The class is explicit: "the model copies your example more carefully than your words." Adding 1–2 hand-drafted exemplar outputs per audience would tighten format adherence and reduce reliance on the model's interpretation of the FORMAT block. Sized as ~2 hours per audience.
- *`max_tokens` not set in `audience_translator.py`.* One-line oversight. Per the class: "a prompt without max_tokens is a runaway bill — and a frozen UI." Currently constrained only by the prompt's policy ("Be concise"). Should be enforced. Sized as 1 line.
- *No explicit escape hatch.* The class recommends a "NOT_IN_SOURCE"-equivalent — an instruction that lets the model say "I don't have this" rather than fabricate. Direct cause of the Week 9 audit-reference fabrication finding: the model invented `[git commit hash]` and `2024-07-30T12:00:00Z` because it had no legal way to signal absent values. Fix: one bullet per CONSTRAINTS block — "If a value required by the FORMAT is not present in the input, write [UNAVAILABLE]. Do not invent placeholder text or example values." Sized as 30 minutes total across three prompts.

*Not applicable to current scope.* Tools, multi-turn assistant history, long-horizon compaction, U-curve management — single-turn audience translation does not exercise these. Re-examine for the Week 10 thin agent build (which is multi-step and may exercise tools).

Implementation of the three gaps lands in Week 10 simplification pass (see §6 Week 10 entry below).

### Week 10 (May 24–28): thin agent + CV warm-up + simplification before features

**Simplification pass — pre-thin-agent (Sun 24 May 2026 AM).** Code is starting to splay: six numbered layers, two corpora that don't share IDs, three external services, and ~700 LOC across `src/` and `app/`. Before any new feature work, four straight-to-point moves that net *reduce* the codebase:

1. *Pre-compute the audit reference in `bundle.py` and surface it in the AUDIT METADATA section of `format_bundle()`.* Closes the audit-reference fabrication issue. Note at execution: neither of the original prompts had an Audit reference: FORMAT slot nor a CONSTRAINTS bullet about audit-reference handling — the Week 9 fabrication ("[git commit hash] / 2024-07-30T12:00:00Z") was the model self-extending the AUDIT METADATA block in user content. The pre-computation half is the actual fix — give the model a concrete fact and the invitation to fabricate one disappears. `_PIPELINE_VERSION` and `_AUDIT_REFERENCE` constants added as module-level; held deterministic (no live timestamp, no git hash lookup) so `format_bundle()` stays bit-identical across calls and the legal harness's temperature-0.0 regression property is preserved. Value: SiteLens-v0.9-w10 / Vescovo2025 / GSI 2024-01-11. Estimated 1 hour.
2. *Add `max_tokens` to `audience_translator.py` per the class-deck audit.* One line. Estimated 5 minutes.
3. *Add an explicit escape hatch (`[UNAVAILABLE]` instruction) to every audience CONSTRAINTS block.* Estimated 30 minutes across three prompts.
4. *Add one or two few-shot examples per audience prompt.* The class-deck audit's largest single gap. Estimated 2 hours per audience for hand-drafted exemplars validated against the existing pass/fail harness.
5. *Replace Layer 5 distilbart with Gemini Flash at temperature 0.3.* Currently downloads ~300MB on cold-start, occupies memory, slows first interaction. Gemini already in the stack for Layer 6; reusing it eliminates one model dependency, no model download, no transformers/torch in runtime. The Layer 5 cross-summary becomes another `translate()`-style call with a fifth "senior coordinator" persona. The architecture note in the Streamlit Layer 5 expander (about t5-rejection) stays as a teaching artefact — the claim that *abstractive ML belongs at Layer 5, not Layer 3* is still true; only the model used changes. Estimated 1 hour.
6. *Unify the corpora — re-index Pinecone against `labels.csv` (the 2,045-record corpus).* Eliminates the schema-resilient `.get()` defaults in `bundle.py` because every retrieved record will have every field. Removes a category of "field X not found" bugs at the seam. Estimated half day.

These six moves net *reduce* the codebase: fewer files (no distilbart loader), fewer defensive branches (no schema-resilient `.get()`), fewer prompt CONSTRAINTS bullets (no audit-reference handling). Right direction before adding the thin agent on top.

**Simplification pass — moves 1–3 landed (Mon 25 May 2026, pre-thin-agent).** Moves 1 (audit-reference pre-computation in `bundle.py`), 2 (`max_tokens` in `audience_translator.py`), and 3 (`[UNAVAILABLE]` escape hatch in all three CONSTRAINTS blocks) executed as planned. Post-patch harness run on the existing `test_records`: all three audiences (insurance / engineering / legal) at 100% pass. Legal at T=0.0 confirmed bit-identical to the pre-patch run — `audit_reference` is surfaced in the AUDIT METADATA section of `format_bundle()`, which the model reads as ambient context rather than a FORMAT slot to fill; the change populates a fact the model was previously self-extending, but does not alter the output token sequence for well-formed records. Bit-identical result also confirms moves 2 and 3 do not perturb legal-audience output for records where all required values are present. Moves 4–6 deferred; not required for the thin-agent build.

**Thin agent build (Mon 25 May 2026).** Bbox-in → report-out wrapper over the existing audience translator. The audience translator does the heavy lifting; the agent is the wrapper. Multi-record case (senior-coordinator audience as one of many per the §4 voice-localisation extension) folded in as the agent's natural multi-record path. Streamlit click-on-marker target selection closes the dropdown-only interaction loop. Delivers Week 10's curriculum requirement (agentic AI / MCP) without scope expansion.

**CV warm-up (Tue–Thu 26–28 May 2026).** Load `data/noto_crops/labels.csv` into `flow_from_dataframe`. Baseline small CNN at 64×64 from the cats-vs-dogs template (per the 18 May CNN recap). Run 5 epochs from scratch with class weights; 5 epochs with MobileNetV2 transfer learning. Plot per-class F1 and AUC. Goal: a baseline number in hand before Week 11 capstone build proper, so the capstone is iteration not from-zero.

**Article-decisions journal setup (Sun 24 May 2026 evening, 30 min).** Create `/article/article_decisions.md` and capture initial framing decisions while fresh: title candidates, argument structure, reference list, parametric-visualization specification (per §1 upstream-justification entry's visual methodology subsection). No real article work — just capture so the framing doesn't get lost between now and post-Demo-Day.

**Open for Wednesday 27 May 2026 (CV mid-week checkpoint).**
- Transfer learning vs train-from-scratch architecture decision (deferred from Week 9). Decide on empirical grounds: per-class F1 on a small validation split, training time per epoch, ease of explanation in the capstone presentation.
- Class imbalance ratio in Wajima crops — confirm after first training run, decide between class weights at training time vs stratified subsampling at extract time.

---

## 7. Evaluation discipline

**Pre-Week-11 commitments (18 May 2026):**

- *Report per-class F1, precision, recall, and confusion matrix — not accuracy.* The class imbalance in Vescovo (destroyed is a small minority of 140,208 buildings) makes accuracy uninformative. A model with 95% accuracy that catches 30% of destroyed buildings is useless for triage; a model with 80% accuracy that catches 90% of destroyed buildings is the product. Per-class metrics are the only honest report.

- *Track model F1 and Vescovo's label-validation F1 separately.* The §4 honest-framing discipline applies: every published number includes both, never conflated. Expected model F1 in the 0.6–0.75 range for image-only binary classification at 64×64; that is a defensible result and the honest one. Quoting Vescovo's 0.94 as the model number is the single most damaging move available.

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
    └── streamlit_app.py            (live on Streamlit Community Cloud)
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

**Closures (19 May 2026).**

- *LLM choice for Week 9 — closed.* Gemini 2.5 Flash via the new `google.genai` SDK with `Client()` pattern. Free-tier rate limit (~10 RPM) operational, manageable with notebook caching. The earlier "split-stack: local distilbart + remote Gemini" plan held — distilbart stays at Layer 5 for generalist cross-summary, Gemini at Layer 6 for audience translation.

- *Multi-input senior summary — closed, reframed.* Delivered as the "senior coordinator" audience persona in the voice-localisation framework (per SR decisions log §4 extension). Multi-record input is handled by the same `translate()` function passing a record list rather than a single record; no separate UI plumbing or feature track.

**New opens (19 May 2026).**

- *Pass/fail harness validation for engineering and legal audiences.* Pattern designed Tuesday; lock-in deferred to Wed 20 May 2026.

- *Layer 2 precedent + Layer 3 narrative wiring into audience bundle.* `translate()` already accepts the arguments; Streamlit integration in Week 10 is the natural moment to wire them up against the existing Pinecone retrieval and rule-based narrator.

- *Evidence-class axis (carried open from Week 8 hackathon, 13 May 2026).* Still open. Becomes natural to surface when (a) the pass/fail harness has visibility into how the model treats single-source vs multi-source records, and (b) Streamlit display can colour-code records by class. Re-evaluate before Week 11 capstone scope is locked.

**Closures (22–24 May 2026).**

- *LLM choice for Week 9 report generator — confirmed.* Gemini 2.5 Flash via the new `google.genai` SDK. Free-tier rate limit (~10 RPM) operational. Distilbart at Layer 5 to be replaced with Gemini Flash during Week 10 simplification pass (entry above) — completes the rationalisation of LLM-model dependencies to one provider, two temperatures.
- *Audit-reference fabrication — closed (Mon 25 May 2026, Move 1).* Week 9 fabrication of `[git commit hash]` / `2024-07-30T12:00:00Z` was the model self-extending the AUDIT METADATA block in user content — neither prompt had an `Audit reference:` FORMAT slot nor a CONSTRAINTS bullet for it, so the failure mode was self-extension, not filling a specified slot. Fix: pre-computed `_AUDIT_REFERENCE` constant surfaced in `format_bundle()` AUDIT METADATA section; no FORMAT change required. Legal T=0.0 post-patch output is bit-identical to pre-patch — confirms `audit_reference` reads as ambient context, not a model-generated FORMAT field. Same failure class as the secondary-peril world-knowledge override (Tue 19 May): the model fills any gap in the structure it perceives; the fix is to leave no gap.
- *Two-corpus seam (Layer 1 labels.csv vs Layer 2 sample_records) — fix scoped.* Bridged via schema-resilient `.get()` patches in `bundle.py` for Week 9 demo; full unification deferred to Week 10 simplification pass (re-index Pinecone against `labels.csv`).
- *Streamlit horizontal scroll — fixed.* Global CSS injection targeting `div[data-testid="stCode"] pre` with `white-space: pre-wrap` and `word-wrap: break-word`. Implemented in `streamlit_app.py` deploy 21 May 2026.

**Closures (25 May 2026).**

- *Week 10 simplification pass, moves 1–3 — landed.* Audit-reference pre-computation (Move 1), `max_tokens` (Move 2), and `[UNAVAILABLE]` escape hatch (Move 3) executed pre-thin-agent. All three audience harnesses (insurance / engineering / legal) at 100% pass on existing `test_records`. Legal T=0.0 bit-identical to pre-patch. Moves 4–6 deferred pending thin-agent completion.

**New opens (24 May 2026).**

- *Architecture infographic for the layered pipeline.* Visual showing six layers, deterministic-vs-LLM call-outs per layer, provenance flow as a side rail, audience fan-out at Layer 6. Reusable asset for Demo-Day presentation, post-Demo-Day article, future Forge / partner conversations. Design system: deck-monochrome plus deep-red accent (#A41E1E), Inter typeface. Scheduled to draft Sun 24 May 2026 PM or Mon 25 May 2026 AM as a 1-hour artefact.
- *Field-fast UX variant (per SR §1 entry on architecture-legible vs field-fast inversion).* Not built; not bootcamp scope. Logged for future product-roadmap awareness — Phase 1 deliverable for SR when partner pilot opens.
- *Layer 2 / Layer 3 wiring into audience-translation bundle.* Currently `translate()` accepts the arguments but the notebook does not pass them. Streamlit integration on 21 May 2026 wires Layer 2 precedents and Layer 3 narrative; notebook still uses isolated `translate()` calls. Low-priority cleanup; notebook is for development not demo.

**Week 11 — Layer-1 classifier complete (6 Jun 2026).**

`model/train.py` and `model/evaluate.py` replaced placeholders with full production scripts. MobileNetV2 (ImageNet-pretrained, frozen backbone, single-logit head) trained on 1,967 deduplicated building crops from `data/noto_crops/all/`. Three fixes surfaced during first run and resolved before results were accepted:

1. *CROPS_DIR path.* Placeholder assumed `data/noto_crops/crops/`; actual extraction output is `data/noto_crops/all/`. Corrected in `train.py` CONFIG block.
2. *`s_fid` type mismatch.* `crop_path()` called `int(s_fid)` but `s_fid` values are compound strings (e.g. `20230303-49281-13461-s-7542`). Filenames are sequential integers assigned at extraction time, not derived from `s_fid`. Fixed by reading `filepath` column directly from `labels.csv` when present; `crop_path()` retained as fallback.
3. *Duplicate `s_fid` rows — leakage risk.* `labels.csv` contained 27 duplicate building IDs. Per-row split without dedup put twin rows on opposite sides of train/test, inflating test-set size from 300 to 322 and exposing ~22 buildings to both training and evaluation. Fixed by `drop_duplicates(subset="s_fid")` in `load_labeled_frame()` before the split. Working set: 1,967 rows.

**Evaluation results (leakage-free held-out test, n = 296, CPU, 30 epochs with patience 6):**

| | precision | recall | F1 |
|---|---|---|---|
| survived | 0.919 | 0.983 | 0.950 |
| destroyed | 0.918 | 0.692 | 0.789 |
| **macro** | **0.919** | **0.837** | **0.870** |

ROC-AUC 0.918. Class imbalance (~3.5:1) handled with `BCEWithLogitsLoss pos_weight` derived from the training split. Test split locked to `model/weights/test_split.csv` on first run; `evaluate.py` always scores the same buildings.

**Correction (27 Aug 2026) — the "locked on first run" claim above is wrong.** It is retained, not overwritten, because it is the record of what was believed when these numbers were accepted. `train.py:161-162` rewrites `test_split.csv` unconditionally on every run; there is no `if SPLIT_OUT.exists()` guard anywhere, and "lock"/"locked" appears only in comments. The split held across reruns only because `SEED=42` is fixed and `load_labeled_frame()` is deterministic. The 0.789 / 0.870 / 0.918 figures above stand — the audit confirmed the split itself is leakage-free. See the code audit below (27 Aug 2026), Correction 1.

Full-dataset predictions written to `data/noto_crops/predictions.csv` for demo wiring (pre-computed lookup; the Streamlit app loads no model live).

*Honest framing enforced in output:* `evaluate.py` prints model F1 and Vescovo et al. 2025 ground-survey F1 = 0.94 side by side with an explicit label that they are different kinds of number. Never conflated.

- *`torchvision` added to requirements.txt.* Missing from requirements despite being a direct dependency of `model/train.py` and `model/evaluate.py`. Installed as `torchvision 0.27.0+cpu`; `requirements.txt` updated to `torchvision>=0.15.0`.
- *README overhauled.* New opening blurb, live-demo badge (deep-red, for-the-badge), Mermaid architecture diagram (deterministic vs model nodes colour-coded), Technical approach section with evaluation table and two-number framing, Status checklist updated to reflect all completed layers.
- *Architecture diagram.* Mermaid flowchart committed to README — zero image-management overhead, GitHub-native rendering, version-controlled. Fulfils the reusable-asset log entry from 24 May 2026.

---

**Week 12 — deployment hardening, UI, submission (7–11 Jun 2026).**

- *Layer-5 summariser moved off distilbart.* distilbart-cnn-12-6 removed from the runtime; the Layer-5 abstractive-summary placement now routes through Gemini 2.5 Flash. This is what brought the deployed app under the Streamlit Community Cloud ~1 GB memory ceiling (no ~300 MB model download on cold start). The "ML summarisation placement" expander is retained in the app as a teaching artefact; the claim that abstractive ML belongs at Layer 5 not Layer 3 still holds, only the model changed. [Note: the earlier `SITELENS_LOCAL_ML` gating idea did not ship; `sentence-transformers`/MiniLM stays in the runtime because the live semantic path needs it. README line 102 still names distilbart and needs a one-line correction.]
- *Dual retrieval confirmed live and parallel* (`streamlit_app.py` ~640–667, commit f6258ef). Building-number or map-click routes to a spatial path via `neighbours_by_distance()` over the local GeoDataFrame, scores in metres, no Pinecone. Free-text routes to a semantic path via all-MiniLM-L6-v2 against Pinecone, top-k cosine. Earlier "distance replaced Pinecone" notes were a misread; both modes ship.
- *Welcome / landing page.* Single-session gated screen (`session_state["entered"]`): brand title, a what-it-does paragraph (Noto, GSI orthophotos + Vescovo labels), "Who it is for" (insurance / structural / legal), and a four-step "How to use it". Pinecone and the embed model are deliberately not initialised until the user clicks "Open the demo", so the landing paints fast and carries fewer cold-start failure surfaces; `st.stop()` after, so the app proper renders only post-entry.
- *Map, two layers.* GSI tile base (attribution carried), fractional zoom, `prefer_canvas`. Layer one: all buildings as a `MarkerCluster` of faint white dots (tooltip = building number) that collapses to a bubble when far and breaks to individuals at zoom ≥ 17. Layer two: the assessed buildings drawn as footprint polygons via `folium.GeoJson` from `polygons.parquet` (`load_polygons()`), filled by damage colour (destroyed #A41E1E, survived #2A7A2A), the selected building outlined white and heavier, with a CircleMarker fallback when a footprint is missing. Per-building popup shows the readable name, retrieval score, record text, and the pre-computed model call (predicted label, P(destroyed), and a check/miss mark against the Vescovo ground-truth label). Adaptive auto-zoom from geographic spread (single building → 18, wider spreads step down toward 13), plus a rendered legend.
- *Map-state handler.* `st_folium` is called with `returned_objects=[]` so folium interactions do not trigger Streamlit reruns. Viewport (centre/zoom) is persisted to session state only when the user actually pans or zooms, so generating a report or changing the target dropdown does not re-zoom. A `_fit_all_run` flag handles st_folium reporting a one-run-stale centre on the forced rerun after ASSESS, trusting computed values on that run. The map column renders before the notes column so click state is ready downstream.
- *Inputs and routing.* Three reconciled entry points: a scenario-preset selectbox (picking one fills the query and zeroes the building number), a building-number input (overrides the description, resolved to `s_fid` via `bldg_index()`), and a free-text query. Mutual-exclusion callbacks (`_clear_query` / `_clear_bldg`) stop number and text competing; `top_k` (1–10) sets the target-plus-neighbours count; ASSESS is the single run trigger, routing the number path to `neighbours_by_distance()` and the text path to semantic retrieval.
- *Audience and report controls (Layer 6).* After ASSESS, an audience selectbox (insurance / structural / legal), a target-building dropdown that sets `layer6_target_id` (which highlights that building white on the map), and a REPORT button that runs the Gemini audience translation for the selected record, with an audit panel exposing the underlying records.
- *Cleanup pass.* Interface decluttered before Demo Day as general practice, removing redundant elements and tightening the layout so the structural gradient reads without noise.
- *Layout — Route B.* Full-width map with the right-hand panel lifted to a translucent fixed overlay via `.st-key-sidepanel { position: fixed !important }` (the `!important` was the specificity fix) plus a JS `querySelector` hook. Brand title "Site" (white) + "Lens" (sensing red) as a reusable constant used on both the landing and demo screens; "AI" dropped from the header.
- *README opening reframed* to lead with self-assembled data and multi-cause attribution (per Marina's "lead with unique contributions"). Data framed as self-assembled (paired and processed open sources), not self-collected.
- *Repo.* Public. Two clean commits (translation layer, then Week 11 classifier + README). "claude" contributor attribution retained as appropriate for a GenAI programme. `app/gradio_demo.py` placeholder deleted; Streamlit Community Cloud is the deployment, Gradio dropped under deadline.
- *DI scope form filed* (Octopus). Corrections at submission: crop count 1,967, F1 figures, FAISS = No, LoRA = No, Streamlit Community Cloud as deployment.

**Demo Day (11 Jun 2026).**

- Presented and submitted. Deployed app: sitelens.streamlit.app. Tutor feedback pending: bootcamp-side capstone review, plus a more detailed competency mapping on my side (expansion of `SiteLens_competency_mapping.md`).
- Demo Day occurred Thu 11 Jun 2026, same day as submission. §5 and the §6 week-table corrected from the placeholder "Sunday 14 June".
- Submission-form residuals at close: portfolio link and job-tracker link. Job tracker — Google Sheet created for immediate submission (10-column template), Huntr preferred long-term; HQ Architects R&D logged as first entry. Portfolio hosting undecided (Notion / Read.cv / GitHub Pages / Cargo / Framer); blocks any application that cites a portfolio link.
- `SiteLens_competency_mapping.md` produced (supervised learning, RAG, embeddings, transformer inference, evaluation discipline, deployment mapped to artefacts) as evidence for the bootcamp homework-requirement appeal. [flagged for the item-2 adjustment pass.]

**Demo Day deck (capstone presentation).**

- Kept as a separate artefact from the Deploy-meetup venture deck; the capstone deck stays SiteLens-framed with Sensing Risk as motivation only, nothing overstated.
- Structure (six-beat narrative from §8 as the spine, final-drafted against the live app): cover; a trajectory / dissipation-gradient slide (footer corrected from a leftover "Sensing Risk · DEPLOY 2 · 2026" to "SiteLens · DI · 2026", the naming-boundary catch); the pipeline slide (Pinecone RAG, confirmed accurate); the retrospective slide (SEMANTIC COLLAPSE, symbol 1.00); the two conceptual slides (irreducible-core / end-argument, and the developments-in-pale roadmap); and the Thanks slide (DI instructors + GenAI & ML cohort credit, contact block; "BOOTACMAP" typo caught and fixed).
- Key findings as presented, separated and never conflated: image-only model F1 0.789 destroyed / 0.870 macro / ROC-AUC 0.918 (n = 296, leakage-free) against Vescovo 0.94 (human ground survey, n = 140,208); semantic collapse on templated descriptions (scores 1.00) drove the building-neighbour path to distance, which also matches how damage clusters physically; duplicate-`s_fid` leakage caught before results were accepted; fire-vs-seismic decomposition (311 fire / 131 seismic of 442 destroyed) as the multi-cause signal; deterministic peril attribution in the pipeline with the LLM confined to register translation; self-assembled GSI + Vescovo data as the honest origin story.
- Delivery: full run-through against the deployed app; graceful-degradation fallback prepared in case Gemini quota or network failed live. Q&A note kept ready, why the semantic path is still live if a reviewer sees the pipeline slide and the retrospective slide together (both retrieval modes ship; the retrospective is scoped to the neighbour path only).
- Rendered in the shared design system (Inter, operational-red #A41E1E for damage only, dissipating emphasis); token definitions live in the SR decisions log, not here.

**Closures (Demo Day).**

- *Two-corpus seam — closed.* Pinecone re-indexed against `labels.csv` via `pipeline/reindex_pinecone.py`; the schema-resilient `.get()` defaults in `bundle.py` are no longer load-bearing. (Supersedes the "deferred to Week 10 simplification pass" line in §10.)
- *`max_tokens` — closed.* `max_output_tokens=2048` set in `audience_translator.py` as the runaway-cost circuit breaker.
- *`[UNAVAILABLE]` escape hatch — closed.* Present in all three audience CONSTRAINTS blocks; the Week 9 audit-reference fabrication class of failure is addressed (audit reference pre-computed, no longer prompted).

**Deferred (live for Sensing Risk / article, or carried as known gaps).**

- *Few-shot exemplars — not done.* All three audience prompts remain zero-shot. The class-deck audit's largest single gap; carried open.
- *Evidence-class axis* (definitive / supportive / subjective). Not built; carried to Sensing Risk Phase 2 and as an article candidate.
- *Field-fast UX variant.* Route B's map-first overlay is a partial step; the full variant remains an SR Phase-1 item.
- *Layer 2/3 notebook wiring.* Notebook still uses isolated `translate()` calls; Streamlit wires them. Low-priority cleanup, non-blocking.

**Capstone status — provisionally closed, 11 Jun 2026.** Build, evaluation, deployment, README, and submission complete. Held provisional pending (1) Marina Wyss feedback, folded as dated patches not a rewrite, (2) bootcamp-side capstone review, and (3) my own competency-mapping expansion. The two-F1 honesty audit across README, deck, LinkedIn, CV, submission is the gate before final close; the README line-102 distilbart correction is the one known accuracy gap going in.

**Code audit — `train.py` / `evaluate.py` (27 Aug 2026).** Read-only forensic audit run ahead of the 6 Sep Technion defence. Seven questions, all answered from code with `file:line` citations. Three closures, two corrections to this log, one new load-bearing finding.

- *Test contamination — closed. The number is clean.* The split structure is three-way, not two-way: `test` is carved from the de-duplicated frame at `train.py:155-156` (`TEST_FRAC=0.15`, `stratify=df["y"]`, `random_state=42`), then `val` is carved from the `train_val` remainder at `train.py:158-159` (`VAL_FRAC=0.15`, `val_rel=0.15/0.85≈0.1765`). Nominal 70/15/15 → train 1,376 / val 295 / test 296. All three are formed after `drop_duplicates(subset="s_fid")` at `train.py:98`. Early stopping (`train.py:197-212`) monitors macro-F1 on `val_loader` (`CropDataset(val, False)`, `train.py:174`); the best-only checkpoint at `train.py:206` is written on val improvement, and `evaluate.py:41` loads exactly that checkpoint. `train.py` never constructs a `test_loader`. The buildings early stopping saw and the buildings in `test_split.csv` are disjoint by construction — the reported macro F1 0.870 carries no early-stopping optimism. `pos_weight` (`train.py:166-168`) is counted from `train` only; neither val nor test rows enter it. Also clean.

- *Threshold — closed. It was never chosen.* Hard-coded literal `0.5` at `evaluate.py:46`, `evaluate.py:81` and `train.py:198`. No named constant, no config, no derivation. A repo-wide search for threshold / cutoff / `roc_curve` / `precision_recall_curve` / youden returns only prose in `README.md:119-120` and unrelated MMI banding. `roc_auc_score` is computed (`evaluate.py:58`) but only printed. No threshold selection exists in this codebase. Since nothing was tuned, test data could not have been used to tune it — the omission is what makes the answer clean.

- *Threshold sweep is cheap — closed.* `predictions.csv` carries `s_fid, true_label, pred_prob, pred_label` across 1,967 rows (the full de-duplicated frame, augmentation off, deterministic). `pred_prob` is a continuous sigmoid rounded to 4 dp. A held-out sweep is an inner join to the 296 `s_fid`s in `test_split.csv` — no re-inference required.

- *Correction 1 — the test split is not locked.* This log states "Test split locked to `model/weights/test_split.csv` on first run." That is not what the code does. `train.py:161-162` writes the file unconditionally on every run; there is no `if SPLIT_OUT.exists()` guard anywhere. "Lock" / "locked" appears only in comments (`train.py:52, 162, 164`). The split is stable across reruns only because `SEED=42` is fixed and `load_labeled_frame()` is deterministic. The consequence is load-bearing for the next experiment: any change to `labels.csv`, to the crop files on disk, or to the split constants silently rewrites the "locked" test set on the next `train.py` run, and a subsequent `evaluate.py` scores a different population while reporting the same metric names. Re-extracting crops — which is exactly what Correction 2 implies — changes `labels.csv`. The 296 `s_fid`s must be frozen as a committed artefact independent of `labels.csv`, and a write-once guard added, *before* any re-extraction. Otherwise the before/after comparison of a resolution experiment is uninterpretable, because the two arms would be scored on different buildings.

- *Correction 2 — the resolution finding.* New, and probably where recall is lost. `IMG_SIZE = 224` (`train.py:54`) and `transforms.Resize((224,224))` (`train.py:105`) match MobileNetV2's ImageNet pretraining dimension, so the network input is correct. The problem is upstream of it. Crops are stored on disk at 64×64. Native extraction windows in `labels.csv` (`window_width`) run from 8.5 px to 408 px, mean ≈ 38 px. Every building — a ~4 m house at 8.5 px and a ~190 m structure at 408 px — is normalised to the same 64×64 raster, then up-sampled again to 224.
  - *Small buildings:* ~8–20 px of real signal interpolated up ~26× in area. Whether a roofline is fragmented or intact is close to unresolvable at that scale.
  - *Large buildings:* 408 px down-sampled to 64 discards ~97% of available pixels before the model ever sees them.

  A 48× dynamic range in real information is collapsed to one tensor shape. The 64×64 intermediate is a lossy bottleneck in both directions, and it is a sampling decision in our pipeline, not a model limitation. This is the same class of defect as the world-vs-pixel squarify bug (§6, 18 May) — geometric fidelity of the sample before the model. One instance was found and fixed; this is a second instance, unfixed. Direct bearing on the destroyed-class recall of 0.692 at precision 0.918: the error-concentration analysis (30–31 Aug) should treat `window_width` as the primary slice axis, not a secondary one.

- *Correction to the planned error analysis — there is no damage grade to slice by.* Vescovo's schema is natively binary: survived (0) / destroyed (1), plus 9 (obstructed) and 99 (missing or inconsistent). There is no graded scale and therefore no binarisation cut with adjacent grades. The ambiguity axis has to come from the `conf` column and from the 37 class-9 obstructed buildings that were dropped at extraction — those are precisely the hard cases, and the model is currently never evaluated on them. Worth stating out loud rather than leaving implicit.

- *Vescovo 0.94 — verified against source, and narrower than this log implies.* Now published as Vescovo et al., ESSD 17, 5259 (2025). The 0.94 is the harmonic F1 between survived and destroyed classes, measuring agreement between the authors' own multi-source visual assessment and independent ground-survey photographs supplied by Tokoha and Tohoku University teams, computed over roughly 40 m corridors around documented survey paths in four settlements plus scattered rural areas. It is not measured across 140,208 buildings — 140,208 is the dataset size. This log and the SR decisions log both pair the two figures in a way that reads as though the F1 spans the full dataset. Both should be amended to: "F1 0.94 on an independently surveyed validation subset; dataset n = 140,208." Second-order but useful: the Vescovo labels are expert image interpretation validated against ground photographs, not ground survey itself. Our model attempts the same visual task the annotators performed, which makes 0.94 a reasonable statement of the human ceiling on this imagery — still not a number to subtract from, but closer in kind than "a different kind of number" conveys.

- *External comparable located — and it is favourable.* Zhang et al., Remote Sensing 17(17):3116 (2025), "Deep Learning-Based Collapsed Building Mapping from Post-Earthquake Aerial Imagery." Same event, same region: trained on Wajima, Machinomachi and Ukai; tested on Suzu (Noto) and Mashiki (Kumamoto 2016). Aerial imagery at 0.2 m/px — 2.35× finer than our GSI z=18 at ~0.47 m/px. Architecture: PVTv2 encoder with an Uncertainty-Guided Fusion decoder. Reported in-domain: recall 79%, precision 68% → collapsed-class F1 ≈ 0.73. Out-of-domain (Mashiki): recall 66%, precision 77%. Ours: destroyed-class F1 0.789, precision 0.918, recall 0.692. Caveats before this is used anywhere: their in-domain test is Suzu, a town outside their training set, which is a harder generalisation test than our within-Wajima held-out split; theirs is area-based segmentation mapping, ours is per-building classification, so the denominators differ. Not a clean "we score higher." What it does support: our number sits inside the published range for this problem on this event, and the precision/recall shape is inverted — they are recall-heavy (0.68/0.79), we are precision-heavy (0.92/0.69). Same task, opposite operating points, which is evidence that the 0.5 threshold is a placement choice rather than a capability ceiling. Also worth noting: their decoder is uncertainty-guided. The direction named in this log as SiteLens's next need is the direction the published work on this event already took.

**Carries forward (27 Aug 2026).**

1. Freeze the 296 test `s_fid`s and add a write-once guard before any re-extraction.
2. Threshold sweep from stored `pred_prob`, held-out rows only.
3. Error analysis with `window_width` as the primary slice.
4. Amend the Vescovo framing in this log and in the SR decisions log §5.

## 11. 2026-08-13

- Watch layer specified: sitelens_watch.sh + systemd user timer (30 min)
  on Fedora; UptimeRobot as the always-on external layer; escalation to
  a headless page-load if plain GET does not register as Streamlit
  activity. Pre-freeze surface checks: Pinecone index alive, Gemini
  fallback fires, cold-session timing, README numbers match
  0.789/0.870/0.918, GSI attribution visible, in-app stale stage-label
  scan. Text-only patches allowed before freeze; no structural
  redeploys.

## 12. 2026-09-01

- **Bulk data relocated to the BRIDGE partition, junctioned back.** Untracked
  local data moved off `C:` to `D:\SRDATA\sitelens\` and replaced with
  directory junctions at the original repo paths, so every relative path in the
  pipeline still resolves:
  - `data\noto_crops\all`  →  `D:\SRDATA\sitelens\noto_crops\all` (2,045 PNGs, 12.8 MB)
  - `data\raw`  →  `D:\SRDATA\sitelens\raw` (Noto GPKG + `test_sample.py`, 47.9 MB)
  - `data\processed`  →  `D:\SRDATA\sitelens\processed` (empty)
  Counts and bytes verified through each junction against the pre-move record;
  `git status` byte-identical before and after; nothing deleted. The deployed
  Streamlit app is unaffected — it reads only the tracked
  `data\noto_crops\{labels,predictions}.csv` and `polygons.parquet`, none of
  which are under a moved path.
- **Transport copy of the checkpoint.** `model\weights\mobilenetv2_noto.pt`
  copied (not moved) to `D:\SRDATA\sitelens\transport\weights\`; the original
  stays in the repo tree. The trained weights are the one non-reproducible
  artefact.
- **Error-analysis scripts landed** under `analysis\error_analysis_20260901\`
  (six scripts + `OUTPUT.txt` + `sweep_results.csv` + a README). Read-only audit
  of `predictions.csv` / `labels.csv` / `test_split.csv`, run 1 Sep 2026,
  reproducible from tracked files alone. **Findings are deliberately not
  transcribed into this log yet — pending a manual walkthrough.**
- **Val split dumped for review.** `analysis\dump_splits.py` reconstructs
  `train.py`'s three-way split (imports `model\train.py`; `load_labeled_frame`
  + the two stratified `train_test_split` calls, `SEED=42`). Reconstructed test
  set verified to match `model\weights\test_split.csv` exactly (296 s_fids).
  Outputs `analysis\splits\{train_ids,val_ids,val_misses}.csv`; `val_misses.csv`
  (19 rows: val destroyed called survived at 0.5) is the eyeball list for the
  disciplined sample review. The test set stays untouched for selection.

---

End of build log v0.

**Crop review — 4 Sep 2026 (Fedora, contact sheet).**
All 19 val misses eyeballed (analysis/review/contact_sheet.html; left 64px
pixel-honest, right bilinear-224 model input). Finding: every miss contains
BOTH a standing and a collapsed structure in frame — the crop never marks
which building the label refers to; the model scores the frame and the
dominant structure wins. Third defect in the family: squarify = aspect,
64px = scale, crop-reference = subject. Status: observation pending the
dominance check (WKT vs window geometry, ~20 min) before "all 19" is
canonical. Corollary: fire-zone success partly re-explained — scene and
building always agree inside the burn area, so the ambiguity is costless
there. Specified experiment, two arms: (A) hard mask outside footprint
polygon (control, destroys relational signal); (B) footprint mask as 4th
channel (scene + subject pointer). Prediction: B > A; the gap measures
neighbour-awareness. Also: the provenance chain (s_fid → WKT → affine →
pixel window) already closes pixel↔structure↔world — the missing piece is
an output schema per flagged building {id, footprint, centroid, evidence
class, p, capture spec} = UAV task packet for the coarse→fine handoff.
Reviewer: DF. First commit from the Fedora environment.

**Crop review — 4 Sep 2026 (Fedora, contact sheet).**
All 19 val misses eyeballed (analysis/review/contact_sheet.html; left 64px
pixel-honest, right bilinear-224 model input). Finding: every miss contains
BOTH a standing and a collapsed structure in frame — the crop never marks
which building the label refers to; the model scores the frame and the
dominant structure wins. Third defect in the family: squarify = aspect,
64px = scale, crop-reference = subject. Status: observation pending the
dominance check (WKT vs window geometry, ~20 min) before "all 19" is
canonical. Corollary: fire-zone success partly re-explained — scene and
building always agree inside the burn area, so the ambiguity is costless
there. Specified experiment, two arms: (A) hard mask outside footprint
polygon (control, destroys relational signal); (B) footprint mask as 4th
channel (scene + subject pointer). Prediction: B > A; the gap measures
neighbour-awareness. Also: the provenance chain (s_fid → WKT → affine →
pixel window) already closes pixel↔structure↔world — the missing piece is
an output schema per flagged building {id, footprint, centroid, evidence
class, p, capture spec} = UAV task packet for the coarse→fine handoff.
Reviewer: DF. First commit from the Fedora environment.
