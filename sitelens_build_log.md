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

**Four faces of rigidity** (Week 11+ map, not today):
- *Input rigidity* — parser assumes exact template format. Loosens with a learned parser or LLM-based field extraction.
- *Coverage rigidity* — only four template fields. Loosens cheaply by extending the template (footprint, centroid, adjacent-damage context).
- *Output rigidity* — finite if/elif tree. Loosens with fine-tuned generation (capstone fine-tuning question).
- *Domain rigidity* — Vescovo schema only. Loosens highest-leverage by ingesting free-form documents (Vescovo paper PDF, MLIT damage manuals).

---

## 7. Evaluation discipline

*Locked before Week 11. Confusion matrix per damage class, weighted vs unweighted F1, train/val/test split discipline, class-imbalance handling, held-out test set protection, baseline-vs-model comparison framing.*

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

---

End of build log v0.
