# Repository Navigation Guide

This document explains where to find things in the ANR EEG Analysis Pipeline repository.

## Repository map

```text
ANR-EEG-Analysis-Pipeline/
├── README.md
├── pyproject.toml
├── CITATION.cff
├── CONTRIBUTORS.md
├── LICENSE
├── src/
│   └── anr_eeg/
├── notebooks/
├── examples/
├── tests/
├── docs/
└── .github/
```

## `README.md`

Start here for the project overview, installation instructions, supported formats, core workflow, citation information, and links to the guided Colab notebook.

## `notebooks/`

This is the easiest entry point for students and researchers who want a guided workflow.

### `ANR_EEG_Colab.ipynb`

The main Google Colab tutorial.

It is intentionally step-by-step rather than fully automatic. Each section explains:
- what the step does;
- why it is needed;
- what to check in the output;
- which settings the researcher may need to change.

## `src/anr_eeg/`

This contains the reusable Python package used by both local Python and Google Colab.

### `io.py`
Loads EEG data and converts ANR Muse CSV recordings to MNE Raw objects.

### `events.py`
Converts ANR recorder event markers to MNE annotations.

### `qc.py`
Calculates technical acquisition-quality metrics.

### `preprocessing.py`
Contains the v1 filtering and optional referencing workflow.

### `spectral.py`
Calculates PSD and relative frequency-band power.

### `export.py`
Creates cleaned FIF files, QC JSON, band-power CSV, and summary JSON.

### `report.py`
Generates the ANR HTML research report with MNE.

## `tests/`

Automated tests for the package.

GitHub Actions runs these tests so contributors can see whether changes break the validated core workflow.

## `examples/`

Contains example configuration information. Do not place participant recordings here.

## `docs/`

Human-readable documentation.

Recommended reading order:

1. `GETTING_STARTED.md`
2. `REPOSITORY_GUIDE.md`
3. `OUTPUTS_AND_INTERPRETATION.md`

## `.github/workflows/`

Contains GitHub Actions configuration.

The test workflow installs the package and runs the automated test suite on changes to the repository.

## `CITATION.cff`

Citation metadata for users who reference the software in academic work.

## `CONTRIBUTORS.md`

Lists the ANR collaborators and Principal Investigator associated with the project.

## `pyproject.toml`

Defines the installable `anr-eeg` Python package and its dependencies.

## Where should I make changes?

- New import format → `src/anr_eeg/io.py`
- Marker handling → `src/anr_eeg/events.py`
- QC → `src/anr_eeg/qc.py`
- Filtering/reference → `src/anr_eeg/preprocessing.py`
- PSD/band-power → `src/anr_eeg/spectral.py`
- Output files → `src/anr_eeg/export.py`
- HTML report → `src/anr_eeg/report.py`
- Colab teaching workflow → `notebooks/ANR_EEG_Colab.ipynb`
- User guidance → `docs/`

Any scientific-code change should be accompanied by an appropriate test in `tests/`.
