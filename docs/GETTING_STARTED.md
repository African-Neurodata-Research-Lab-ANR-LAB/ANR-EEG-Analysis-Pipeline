# Getting Started with the ANR EEG Analysis Pipeline

The **ANR EEG Analysis Pipeline** is a reproducible EEG research workflow developed by the African NeuroData Research Lab (ANR) and powered by MNE-Python.

This guide is the best starting point if you are new to the repository.

## Fastest route: Google Colab

You do not need to install Python locally.

1. Open the repository on GitHub.
2. Open `notebooks/ANR_EEG_Colab.ipynb`.
3. Click **Open in Colab** if shown, or open the notebook through Google Colab.
4. Run the notebook **one cell at a time**.
5. Read the explanation before each cell.
6. Upload your EEG dataset at the upload step.
7. Inspect the output before moving to the next step.
8. Download the generated ANR result package at the end.

Direct Colab URL:

`https://colab.research.google.com/github/African-Neurodata-Research-Lab-ANR-LAB/ANR-EEG-Analysis-Pipeline/blob/main/notebooks/ANR_EEG_Colab.ipynb`

## Recommended input

The primary format is the CSV exported by the ANR Muse EEG Recorder.

Expected EEG columns:

- `TP9_uV`
- `AF7_uV`
- `AF8_uV`
- `TP10_uV`

At least one usable timestamp source is required for automatic sampling-rate estimation.

The optional `event_marker` column is converted into MNE annotations.

## What the guided notebook does

The workflow is intentionally sequential:

1. Install ANR EEG from GitHub.
2. Import the analysis libraries.
3. Upload one dataset.
4. Load the recording into MNE.
5. Inspect raw EEG.
6. Run technical QC.
7. Select preprocessing settings.
8. Preprocess.
9. Inspect processed EEG.
10. Compute PSD.
11. Compute relative delta/theta/alpha/beta power.
12. Review event markers.
13. Export results.
14. Generate an HTML report.
15. Download the complete output package.

## Local installation

Clone the repository:

```bash
git clone https://github.com/African-Neurodata-Research-Lab-ANR-LAB/ANR-EEG-Analysis-Pipeline.git
cd ANR-EEG-Analysis-Pipeline
```

Create a Python 3.11+ environment and install:

```bash
python -m pip install -e .
```

For development/testing:

```bash
python -m pip install -e ".[test]"
pytest -q
```

## Research-use boundary

The pipeline is intended for research analysis and reproducible workflows. QC status, spectral plots, band power, and reports are not clinical EEG interpretations or diagnoses.
