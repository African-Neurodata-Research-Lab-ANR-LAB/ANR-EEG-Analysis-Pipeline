import json
from anr_eeg import load_eeg, run_qc


def test_qc_returns_serializable_summary(muse_csv):
    raw = load_eeg(muse_csv)
    qc = run_qc(raw)
    assert qc["channel_count"] == 4
    assert qc["sampling_frequency_hz"] == 256.0
    assert qc["duration_seconds"] >= 10.0
    assert qc["status"] in {"pass", "review", "fail"}
    assert set(qc["channels"]) == {"TP9", "AF7", "AF8", "TP10"}
    json.dumps(qc)


def test_clean_synthetic_recording_passes(muse_csv):
    raw = load_eeg(muse_csv)
    assert run_qc(raw)["status"] == "pass"
