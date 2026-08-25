import numpy as np
from anr_eeg import load_eeg, compute_psd, compute_band_power


def test_psd_frequency_range(muse_csv):
    raw = load_eeg(muse_csv)
    spec = compute_psd(raw, fmin=1, fmax=40)
    _, freqs = spec.get_data(return_freqs=True)
    assert freqs.min() >= 1
    assert freqs.max() <= 40


def test_band_power_returns_four_channels_and_four_bands(muse_csv):
    raw = load_eeg(muse_csv)
    result = compute_band_power(raw)
    assert list(result.index) == ["TP9", "AF7", "AF8", "TP10"]
    assert list(result.columns) == ["delta", "theta", "alpha", "beta"]
    assert np.allclose(result.sum(axis=1), 1.0, atol=0.03)
    assert result.loc["TP9", "alpha"] > 0.8
