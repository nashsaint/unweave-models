# Model attribution

The model weights are derived from Meta's Demucs v4 (`htdemucs` and
`htdemucs_6s`), distributed under the MIT licence. Copyright (c) Meta Platforms,
Inc. and affiliates. The full licence is included in LICENSE and in each archive.

Original project: https://github.com/facebookresearch/demucs

Unweave converts the separator network to FP32 Core ML. The exported network
accepts waveform (`mix`) and spectrogram (`spec`) inputs and returns frequency
(`freq`) and waveform (`time`) outputs. Spectrogram analysis, synthesis,
normalization, and overlap-add are handled by Unweave's Swift engine. These are
not drop-in replacements for Core ML exports that accept only waveform input.

The downloadable `.mlpackage` is compiled with Core ML on the user's Mac during
installation. No Python or model conversion environment is needed by the app.

Conversion tooling uses PyTorch, Demucs, coremltools, NumPy, and einops. These
build-time tools are not included in the model archives.
