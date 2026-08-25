import pandas as pd
import pytest
from anr_eeg import load_eeg


def test_load_muse_csv_creates_mne_raw(muse_csv):
    raw = load_eeg(muse_csv)
    assert raw.ch_names == ["TP9", "AF7", "AF8", "TP10"]
    assert raw.info["sfreq"] == 256.0
    assert raw.n_times == 2560
    assert raw.get_data().max() < 0.001


def test_uv_is_converted_to_volts(muse_csv):
    raw = load_eeg(muse_csv)
    assert 15e-6 < raw.get_data(picks=["TP9"]).max() < 25e-6


def test_missing_muse_channel_raises(muse_csv):
    df = pd.read_csv(muse_csv).drop(columns=["AF8_uV"])
    df.to_csv(muse_csv, index=False)
    with pytest.raises(ValueError, match="AF8_uV"):
        load_eeg(muse_csv)


def test_unsupported_format_raises(tmp_path):
    p = tmp_path / "x.xyz"
    p.write_text("x")
    with pytest.raises(ValueError, match="Unsupported"):
        load_eeg(p)
