# Understanding ANR EEG Outputs

The ANR EEG Analysis Pipeline produces technical and research-analysis outputs. This guide explains what each output is for and what it does not mean.

## Technical QC

The QC module reports properties of the acquired recording such as:
- channel count;
- sampling frequency;
- duration;
- standard deviation;
- peak-to-peak amplitude;
- flat-channel flags;
- high-amplitude review flags;
- annotation count.

Overall status may be:
- `pass`
- `review`
- `fail`

These labels refer to acquisition/data quality. They do not describe whether a participant's brain activity is medically normal or abnormal.

## Cleaned FIF

`*_clean_raw.fif`

An MNE FIF copy of the preprocessed EEG. It preserves the MNE object structure for future analysis.

## QC JSON

`*_qc.json`

Machine-readable technical QC results.

Useful for:
- reproducibility;
- batch summaries;
- later report generation;
- tracking technical recording characteristics.

## Band-power CSV

`*_band_power.csv`

Contains relative power for:
- delta: 1–4 Hz;
- theta: 4–8 Hz;
- alpha: 8–13 Hz;
- beta: 13–30 Hz.

Values are normalized to total 1–30 Hz power for each EEG channel.

Relative band power should be interpreted in the context of the experimental task, participant state, recording quality, preprocessing choices, and study design.

## Summary JSON

`*_summary.json`

Contains a compact record of the analysis session and generated file names.

## HTML Report

`*_report.html`

A human-readable research report generated using MNE Report.

It combines technical recording information, QC, frequency-domain results, and event information.

## PSD plot

The power spectral density shows how signal power is distributed across frequency.

A spectral peak is not, on its own, a diagnosis or proof of a physiological condition.

## Event annotations

ANR Muse Recorder markers are converted into MNE annotations.

Always verify:
- marker descriptions;
- event timing;
- task protocol;
- synchronization assumptions

before performing event-related analysis.

## Data protection

Do not commit participant EEG recordings or identifying participant information to the public GitHub repository.

Use non-identifying session codes for research workflows.
