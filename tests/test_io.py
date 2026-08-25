import json

import pandas as pd
import pytest

from anr_eeg import load_eeg


def test_load_muse_csv_creates_mne_raw(muse_csv):
    raw = load_eeg(muse_csv)

    assert raw.ch_names == [
        "TP9",
        "AF7",
        "AF8",
        "TP10",
    ]
    assert raw.info["sfreq"] == 256.0
    assert raw.n_times == 2560
    assert raw.get_data().max() < 0.001


def test_uv_is_converted_to_volts(muse_csv):
    raw = load_eeg(muse_csv)

    assert (
        15e-6
        < raw.get_data(picks=["TP9"]).max()
        < 25e-6
    )


def test_missing_muse_channel_raises(muse_csv):
    df = pd.read_csv(muse_csv).drop(
        columns=["AF8_uV"]
    )
    df.to_csv(muse_csv, index=False)

    with pytest.raises(
        ValueError,
        match="AF8_uV",
    ):
        load_eeg(muse_csv)


def test_sample_index_fallback_uses_muse_default_256_hz(
    muse_csv,
):
    df = pd.read_csv(muse_csv).drop(
        columns=["timestamp_ms", "iso_time"]
    )
    df.to_csv(muse_csv, index=False)

    raw = load_eeg(muse_csv)
    metadata = json.loads(
        raw.info["description"]
    )

    assert raw.info["sfreq"] == 256.0
    assert metadata["timing_source"] == "sample_index"
    assert (
        metadata["sampling_rate_source"]
        == "muse_default"
    )


def test_nonconsecutive_sample_index_without_timestamps_raises(
    muse_csv,
):
    df = pd.read_csv(muse_csv).drop(
        columns=["timestamp_ms", "iso_time"]
    )

    df.loc[500, "sample_index"] = 700
    df.to_csv(muse_csv, index=False)

    with pytest.raises(
        ValueError,
        match="consecutive sample_index",
    ):
        load_eeg(muse_csv)


def test_user_supplied_sfreq_allows_missing_timing_columns(
    muse_csv,
):
    df = pd.read_csv(muse_csv).drop(
        columns=[
            "timestamp_ms",
            "iso_time",
            "sample_index",
        ]
    )

    df.to_csv(muse_csv, index=False)

    raw = load_eeg(
        muse_csv,
        sfreq=256.0,
    )

    metadata = json.loads(
        raw.info["description"]
    )

    assert raw.info["sfreq"] == 256.0
    assert (
        metadata["sampling_rate_source"]
        == "user_supplied"
    )


def test_unsupported_format_raises(tmp_path):
    p = tmp_path / "x.xyz"
    p.write_text("x")

    with pytest.raises(
        ValueError,
        match="Unsupported",
    ):
        load_eeg(p)
