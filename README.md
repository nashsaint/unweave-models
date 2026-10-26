# Unweave models

Public model downloads for Unweave's first-launch setup. The app can download
these files directly from GitHub; no account or nashsaint.com model hosting is
needed. Model weights are attached to versioned GitHub Releases, not committed
into Git history.

This repository lives at `~/Plugins/unweave-models`, separately from the app.

## Prepare a release

Build the FP32 model exports in the Unweave app repository using its
`tool/make_models.sh`, then package them here:

```sh
python3 scripts/package_models.py \
  --source "$HOME/Apps/unweave/tool/model/out32" --tag models-v1
python3 scripts/verify_models.py dist/models-v1 models-v1
```

The packager creates two ZIP archives, `manifest.json`, and `SHA256SUMS` under
`dist/models-v1/`. The archives contain portable `.mlpackage` models rather than
machine-compiled caches. The app verifies each archive, extracts it, and compiles
the model with Core ML on the user's Mac. Model metadata and licence notices
travel with each archive. Conversion itself happens at release time, not on the
user's machine.

## Publish to GitHub

Install GitHub CLI (`brew install gh`) and authenticate (`gh auth login`). Commit
and push this repository's source, then run:

```sh
scripts/publish_models.sh models-v1
```

The publisher verifies the assets, uploads them to a draft release, and publishes
only after every upload succeeds. It can resume a draft upload. Published tags
are never overwritten; use a new version for changed models.

## Download locations

Once `models-v1` is published, its pinned URLs are:

- https://github.com/nashsaint/unweave-models/releases/download/models-v1/manifest.json
- https://github.com/nashsaint/unweave-models/releases/download/models-v1/htdemucs-fp32.zip
- https://github.com/nashsaint/unweave-models/releases/download/models-v1/htdemucs_6s-fp32.zip

The app should pin the model version and expected checksums, verify completed
downloads, and retain installed models in Application Support across updates.
The manifest describes `unweave-split-core-v1`: FP32 inputs `mix` and `spec`,
outputs `freq` and `time`. These are not generic waveform-only Core ML models.

## Tests

```sh
python3 -m unittest discover -s tests -v
swift scripts/check_models.swift dist/models-v1  # compile and load the actual downloads
```

See LICENSE and THIRD_PARTY_NOTICES.md for model attribution.
