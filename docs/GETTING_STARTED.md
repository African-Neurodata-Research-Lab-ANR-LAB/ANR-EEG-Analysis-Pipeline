# Getting Started with the ANR EEG Analysis Pipeline

The **ANR EEG Analysis Pipeline** is a reproducible EEG research workflow developed by the African NeuroData Research Lab (ANR) and powered by MNE-Python.

## Fastest route: Google Colab

You do not need to install Python locally.

1. Open `notebooks/ANR_EEG_Colab.ipynb`.
2. Open it in Google Colab.
3. Run the notebook **one cell at a time**.
4. Read the explanation before each cell.
5. At the upload step, preferably upload the single `*_MNE_READY.zip` produced by the ANR Muse EEG Recorder.
6. Alternatively, upload the matching raw EEG CSV, events TSV, and metadata JSON together.
7. Inspect each output before continuing.
8. Download the generated ANR analysis results at the end.

Direct Colab URL:

`https://colab.research.google.com/github/African-Neurodata-Research-Lab-ANR-LAB/ANR-EEG-Analysis-Pipeline/blob/main/notebooks/ANR_EEG_Colab.ipynb`

## Preferred ANR input

```text
ANR_<session>_<timestamp>_MNE_READY.zip
```

The package contains:

```text
*_raw_eeg.csv
*_events.tsv
*_eeg_metadata.json
```

The metadata sampling frequency and deterministic `sample_index/time_s` relationship are used for MNE reconstruction.

Read [`MNE_READY_INPUT.md`](MNE_READY_INPUT.md) for the full input specification.

## Other supported inputs

The pipeline continues to support:

- legacy ANR Muse CSV;
- EDF/BDF;
- FIF;
- BrainVision;
- BIDS through the Python API.

## Guided workflow

1. Install ANR EEG from GitHub.
2. Import analysis libraries.
3. Upload a dataset/package.
4. Load into MNE.
5. Inspect raw EEG.
6. Run technical QC.
7. Choose preprocessing settings.
8. Preprocess.
9. Inspect processed EEG.
10. Compute PSD.
11. Compute relative band power.
12. Review event annotations.
13. Export standardized outputs.
14. Generate an HTML report.
15. Download results.

## Local installation

```bash
git clone https://github.com/African-Neurodata-Research-Lab-ANR-LAB/ANR-EEG-Analysis-Pipeline.git
cd ANR-EEG-Analysis-Pipeline
python -m pip install -e .
```

For development/testing:

```bash
python -m pip install -e ".[test]"
pytest -q
```

## Research-use boundary

QC status, EEG spectra, band power, event annotations, and reports are research outputs. They are not clinical EEG interpretations or diagnoses.
