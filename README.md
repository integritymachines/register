# Register: Class-D prediction pipeline

This repository reproduces the complete speculative D300 roll-call experiment:

1. Read the fixed 300-author predictive manifest, 48-pair lexicon, and frozen
   D24 background templates.
2. Produce the first-pass Class-D panel without consulting measured A/B or C
   data, coordinates, or projections.
3. Fill every remaining abstention with an explicitly labeled speculative
   estimate.
4. Validate all 14,400 author × pair cells and freeze the outputs with SHA-256
   hashes.

Run from a clean checkout with Python 3.10 or later:

```bash
python generate_d300_predictions.py \
  --output-dir D300_predictions_full \
  --archive D300_predictions_full.zip
```

The main result is `D300_predictions_full/D300_ROLLCALL_FULL.csv`. The pipeline
has no third-party Python dependencies. Direct 10D conversion is deliberately
outside its scope.

The predictions are structured, very-low-confidence hypotheses rather than
corpus measurements. The fixed inputs and both transparent generation stages
are committed so the experiment can be audited and rerun.
