# ANR EEG Analysis Pipeline

**African NeuroData Research Lab (ANR)**

[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/African-Neurodata-Research-Lab-ANR-LAB/ANR-EEG-Analysis-Pipeline/blob/main/notebooks/ANR_EEG_Colab.ipynb)

A reproducible, MNE-Python-powered EEG research workflow developed by the African NeuroData Research Lab.

The pipeline is designed around a simple idea:

**record EEG → understand the data → check acquisition quality → preprocess → analyze frequency content → export reproducible results**

The primary input format is the CSV produced by the ANR Muse EEG Recorder, while common MNE-compatible formats are also supported.

---

## Start here

### I want to analyze EEG without installing anything

Open the guided Google Colab notebook:

**[`notebooks/ANR_EEG_Colab.ipynb`](notebooks/ANR_EEG_Colab.ipynb)**

The notebook is deliberately **step by step**. Run one cell, inspect the result, read the explanation, and then continue.

It guides you through:

1. installing the latest ANR pipeline from this GitHub repository;
2. uploading your EEG recording;
3. loading the recording into MNE;
4. inspecting channels and recording information;
5. viewing raw EEG;
6. running technical QC;
7. selecting preprocessing settings;
8. preprocessing the EEG;
9. viewing PSD;
10. calculating relative band power;
11. reviewing event markers;
12. exporting research outputs;
13. generating an HTML report;
14. downloading the complete result package.

### I want to understand the repository first

Read the documentation in this order:

1. **[Getting Started](docs/GETTING_STARTED.md)**
2. **[Repository Navigation Guide](docs/REPOSITORY_GUIDE.md)**
3. **[Outputs and Interpretation](docs/OUTPUTS_AND_INTERPRETATION.md)**

---

## ANR Muse EEG input

The ANR Muse EEG Recorder CSV is the first-class input format.

Expected EEG columns:

```text
TP9_uV
AF7_uV
AF8_uV
TP10_uV
```

The loader also uses:

```text
timestamp_ms
iso_time
event_marker
```

when available.

The pipeline converts Muse values from microvolts to volts for MNE and converts ANR event markers into MNE annotations.

---

## Current v1 workflow

```text
ANR Muse EEG CSV
        ↓
Input validation
        ↓
MNE Raw object
        ↓
Technical QC
        ↓
Notch filtering
        ↓
1–40 Hz band-pass
        ↓
Optional re-referencing
        ↓
Welch PSD
        ↓
Relative band power
        ↓
Event review
        ↓
FIF + CSV + JSON + HTML report
```

### Frequency bands

| Band | Range |
|---|---:|
| Delta | 1–4 Hz |
| Theta | 4–8 Hz |
| Alpha | 8–13 Hz |
| Beta | 13–30 Hz |

Band-power values are calculated relative to total 1–30 Hz power for each channel.

---

## Supported formats

### Primary
- ANR Muse Recorder CSV

### Secondary through MNE
- EDF
- BDF
- FIF
- BrainVision

### BIDS
BIDS EEG can be loaded through the Python API with MNE-BIDS.

---

## Install directly from GitHub

Because GitHub is the source of truth, users can install the current pipeline directly:

```bash
pip install "git+https://github.com/African-Neurodata-Research-Lab-ANR-LAB/ANR-EEG-Analysis-Pipeline.git"
```

Then:

```python
from anr_eeg import (
    load_eeg,
    run_qc,
    preprocess,
    compute_psd,
    compute_band_power,
    export_results,
    make_report,
)
```

Example:

```python
raw = load_eeg("ANR_recording.csv")
qc = run_qc(raw)
clean = preprocess(raw, l_freq=1.0, h_freq=40.0, notch=50.0)
bands = compute_band_power(clean)
```

---

## Repository structure

```text
ANR-EEG-Analysis-Pipeline/
├── README.md
├── pyproject.toml
├── CITATION.cff
├── CONTRIBUTORS.md
├── src/
│   └── anr_eeg/
│       ├── io.py
│       ├── events.py
│       ├── qc.py
│       ├── preprocessing.py
│       ├── spectral.py
│       ├── export.py
│       └── report.py
├── notebooks/
│   └── ANR_EEG_Colab.ipynb
├── docs/
├── examples/
├── tests/
└── .github/
```

See **[Repository Navigation Guide](docs/REPOSITORY_GUIDE.md)** for what each file does.

---

## Outputs

A standard analysis can produce:

- cleaned MNE FIF recording;
- technical QC JSON;
- relative band-power CSV;
- analysis summary JSON;
- MNE HTML research report.

See **[Outputs and Interpretation](docs/OUTPUTS_AND_INTERPRETATION.md)** before interpreting results.

---

## Run locally

Requires Python 3.11 or newer.

```bash
git clone https://github.com/African-Neurodata-Research-Lab-ANR-LAB/ANR-EEG-Analysis-Pipeline.git
cd ANR-EEG-Analysis-Pipeline
python -m pip install -e .
```

Run tests:

```bash
python -m pip install -e ".[test]"
pytest -q
```

---

## Built on MNE-Python

ANR EEG uses MNE-Python as its scientific neurophysiology engine rather than reimplementing the underlying EEG algorithms.

ANR adds the research workflow layer around MNE:
- ANR Muse Recorder compatibility;
- marker handling;
- standardized QC;
- preprocessing presets;
- beginner-friendly Colab guidance;
- standardized ANR exports and reports.

---

## Project team

### Collaborators
- Duruh Joseph
- Samuel Akingbulu
- Deborah Eseurhobo
- Christopher Ogbe
- Angelic Charles
- Esther Bassey
- Smart Oparaugo
- Barisua Nsaane
- Goodness Naabie
- Patrick Filima

### Principal Investigator
- **Dr. Eberechi Wogu**

See [`CONTRIBUTORS.md`](CONTRIBUTORS.md) and [`CITATION.cff`](CITATION.cff) for project attribution.

---

## Data governance

Do not commit participant EEG recordings, names, clinical records, or personally identifying research data to this public repository.

Use non-identifying research/session codes.

---

## Research-use statement

The ANR EEG Analysis Pipeline is intended for research, training, and reproducible neurophysiology workflows.

Technical QC statuses, EEG spectra, band power, plots, and reports are **not clinical EEG interpretation and do not provide diagnosis**.

---

**African NeuroData Research Lab (ANR)**  
https://africanneurodataresearch.org/  
Research enquiries: anrlab.ng@gmail.com
