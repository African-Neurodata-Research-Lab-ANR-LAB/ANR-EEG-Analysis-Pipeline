import numpy as np
import pytest
from anr_eeg import load_eeg, preprocess


def test_preprocess_returns_copy(muse_csv):
    raw = load_eeg(muse_csv)
    before = raw.get_data().copy()
    clean = preprocess(raw, notch=None)
    assert clean is not raw
    assert np.array_equal(raw.get_data(), before)


def test_preprocess_rejects_frequency_above_nyquist(muse_csv):
    raw = load_eeg(muse_csv)
    with pytest.raises(ValueError, match="Nyquist"):
        preprocess(raw, h_freq=200)


def test_notch_and_bandpass_execute(muse_csv):
    raw = load_eeg(muse_csv)
    clean = preprocess(raw, notch=50.0, l_freq=1.0, h_freq=40.0)
    assert clean.n_times == raw.n_times
    assert clean.ch_names == raw.ch_names
