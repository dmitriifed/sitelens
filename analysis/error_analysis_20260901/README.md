# Error analysis — 1 Sep 2026

A read-only audit of the shipped Layer-1 classifier, run 1 September 2026 against
the tracked evaluation artefacts only: `data/noto_crops/predictions.csv`,
`data/noto_crops/labels.csv`, and the locked `model/weights/test_split.csv`. The
six scripts (`repro.py`, `sweep.py`, `errors.py`, `interact.py`, `baseline.py`,
`mechanism.py`) reproduce the published test metrics, sweep the decision
threshold, slice destroyed-class recall by building size / hazard class /
municipality / label confidence, and probe how far the model's output tracks the
GSI fire flag; `OUTPUT.txt` is the captured console run and `sweep_results.csv`
the threshold table. Nothing here trains or writes model state and no input is
read that is not already committed, so the audit is reproducible from tracked
files alone. The findings are still under manual review and are deliberately
**not** transcribed into `sitelens_build_log.md` yet — see the build log once the
walkthrough is complete.
