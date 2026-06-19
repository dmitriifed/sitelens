# SiteLens AI — Curriculum Competency Mapping

A mapping of the program's learning objectives to where each is demonstrated in
the capstone. The intent is to show that the project exercises the curriculum as
one integrated, working system rather than as isolated exercises.

Repository: https://github.com/dmitriifed/sitelens · Live demo: https://sitelens.streamlit.app

---

## Core machine learning

| Competency | Where it is demonstrated in SiteLens |
|---|---|
| Supervised learning | MobileNetV2 transfer-learning classifier (destroyed / survived), trained on 1,967 labelled per-building crops. |
| Feature engineering | Per-building crop extraction with provenance, image normalisation, and class-weighting for a 3.57:1 class imbalance. |
| Loss function | `BCEWithLogitsLoss` with `pos_weight` derived from the training split to handle the imbalance. |
| Overfitting (diagnosis & control) | Frozen pretrained backbone, data augmentation, and early stopping on validation macro-F1; train/val curves monitored. |
| Regularisation | Transfer learning, augmentation, and early stopping as complementary regularisers. |
| Model evaluation | Leakage-free held-out test split (deduplicated by building id), per-class precision/recall/F1, confusion matrix, ROC-AUC. Results reported honestly: model F1 (destroyed 0.79, macro 0.87) stated separately from the ground-survey benchmark (0.94), never conflated. |

## Generative AI and LLMs

| Competency | Where it is demonstrated in SiteLens |
|---|---|
| Vector embeddings | `sentence-transformers/all-MiniLM-L6-v2` for semantic representation of building records. |
| Vector database | Pinecone (serverless) holding 1,967 indexed records with metadata. |
| Retrieval-Augmented Generation | Query/anchor → vector retrieval → LLM report generation as an end-to-end RAG pipeline. |
| Transformer inference | Gemini 2.5 Flash for audience-specific report generation and cross-assessment summary. |
| Tokenisation | Embedding and LLM tokenisation as part of the retrieval and generation stages. |
| Prompt engineering | Audience-specific translation prompts (insurance / structural engineering / legal); deterministic facts passed to the model as context rather than derived inside the prompt. |
| Agentic AI / context engineering | Deterministic-where-derivable, generative-where-judgment-is-needed pipeline design; pre-computed facts materialised and fed forward as attributable context. |

## Data and engineering

| Competency | Where it is demonstrated in SiteLens |
|---|---|
| Python | Entire codebase — data pipeline, model training/evaluation, and application. |
| APIs | Integration with the Gemini API, Pinecone API, and the GSI map-tile service. |
| JSON | Provenance records, audit trail, and pre-computed prediction lookups. |
| Data wrangling | Label processing, deduplication, stratified train/val/test splits, and spatial nearest-neighbour computation (pandas/numpy). |

## Software practice and deployment

| Competency | Where it is demonstrated in SiteLens |
|---|---|
| Deployment | Streamlit Community Cloud; secrets/environment management; memory-footprint optimisation (offline batch inference, lazy/gated model loading). |
| Interactive application | Folium/Leaflet map with zoom-aware clustering, per-building drill-down, and predicted-vs-actual display. |
| Version control & documentation | GitHub repository, README technical write-up, architecture diagram, and a reproducible re-index script. |

---

*Each row corresponds to a deliverable that can be inspected directly in the
repository. The project is presented honestly: performance figures are reported
against a leakage-free test split and are never overstated relative to the
ground-truth benchmark.*
