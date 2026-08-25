# Analysis-pipeline patch

Replace/add:

- `src/anr_eeg/io.py`
- `tests/test_mne_ready_bundle.py`
- `notebooks/ANR_EEG_Colab.ipynb`
- `docs/GETTING_STARTED.md`
- `docs/MNE_READY_INPUT.md`

The loader now accepts:
- ANR MNE-ready ZIP directly;
- the three extracted package files;
- legacy ANR Muse CSV;
- the previously supported standard MNE formats.
