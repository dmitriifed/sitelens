"""
run_inference.py — End-to-end inference pipeline.

Part of SiteLens AI. Weeks 11-12 deliverable.

Given a bounding box, runs the full SiteLens pipeline:
  1. Fetch GSI tiles (data/fetch_gsi_tiles.py)
  2. Extract per-building crops (data/crop_extractor.py)
  3. Classify damage (model/)
  4. Generate inspection report (report/generator.py)
  5. Return structured output for Gradio demo or CLI
"""

# TODO: implement in Weeks 11-12
