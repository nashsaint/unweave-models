FP32 Core ML separator models for Unweave on macOS 14 and later:

- `htdemucs-fp32.zip`: four stems — drums, bass, other, vocals.
- `htdemucs_6s-fp32.zip`: six stems — adds guitar and piano.
- `manifest.json`: version, download sizes, SHA-256 checksums, and engine metadata.
- `SHA256SUMS`: checksums for both archives and the manifest.

Each archive contains a portable `.mlpackage`, model metadata, the MIT licence,
and attribution. Unweave compiles the package on the user's Mac after download.
These models use the `unweave-split-core-v1` interface and require Unweave's
spectrogram processing. Audio separation runs locally after initial setup.
