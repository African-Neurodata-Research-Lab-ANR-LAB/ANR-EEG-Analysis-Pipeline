import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def muse_csv(tmp_path):
    sfreq = 256.0
    n = 2560
    t = np.arange(n) / sfreq
    timestamp_ms = 1_800_000_000_000 + t * 1000
    df = pd.DataFrame({
        "timestamp_ms": timestamp_ms,
        "iso_time": pd.to_datetime(timestamp_ms, unit="ms", utc=True).astype(str),
        "sample_index": np.arange(n),
        "session_code": "ANR-TEST",
        "protocol": "resting",
        "stop_reason": "",
        "TP9_uV": 20 * np.sin(2*np.pi*10*t),
        "AF7_uV": 15 * np.sin(2*np.pi*8*t),
        "AF8_uV": 12 * np.sin(2*np.pi*6*t),
        "TP10_uV": 18 * np.sin(2*np.pi*12*t),
        "event_marker": "",
    })
    df.loc[256, "event_marker"] = "AUTO: eyes_closed"
    df.loc[257, "event_marker"] = "AUTO: eyes_closed"
    df.loc[1280, "event_marker"] = "MANUAL: task_start"
    path = tmp_path / "muse.csv"
    df.to_csv(path, index=False)
    return path
