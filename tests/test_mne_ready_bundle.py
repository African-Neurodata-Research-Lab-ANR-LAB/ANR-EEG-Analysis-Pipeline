import json, zipfile
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from anr_eeg import load_eeg

def make_bundle(tmp_path, bad_time=False):
    prefix="ANR_ANR-001_2026-08-25T14-18-28-887Z"
    csv_path=tmp_path/f"{prefix}_raw_eeg.csv"
    events_path=tmp_path/f"{prefix}_events.tsv"
    meta_path=tmp_path/f"{prefix}_eeg_metadata.json"
    n=512; sfreq=256.0
    idx=np.arange(n); time_s=idx/sfreq
    if bad_time: time_s[100]+=0.01
    df=pd.DataFrame({
        "sample_index":idx, "time_s":time_s,
        "timestamp_ms":1_800_000_000_000+time_s*1000,
        "iso_time":pd.to_datetime(1_800_000_000_000+time_s*1000,unit="ms",utc=True).astype(str),
        "session_code":"ANR-001","protocol":"Resting state","stop_reason":"stopped by researcher",
        "TP9_uV":np.sin(2*np.pi*10*time_s)*20,
        "AF7_uV":np.sin(2*np.pi*8*time_s)*15,
        "AF8_uV":np.sin(2*np.pi*6*time_s)*12,
        "TP10_uV":np.sin(2*np.pi*12*time_s)*18,
        "event_marker":""
    })
    df.to_csv(csv_path,index=False)
    pd.DataFrame([
        {"onset":0.5,"duration":0.0,"description":"AUTO: Eyes closed","source":"auto"},
        {"onset":1.5,"duration":0.0,"description":"MANUAL: task_start","source":"manual"},
    ]).to_csv(events_path,sep="\t",index=False)
    meta={
        "format":"ANR Muse EEG MNE-ready","format_version":"1.0",
        "sampling_frequency_hz":256,
        "mne_time_source":"sample_index / sampling_frequency_hz",
        "channel_names":["TP9","AF7","AF8","TP10"],
        "channel_types":["eeg"]*4,"units":"microvolts",
        "eeg_file":csv_path.name,"events_file":events_path.name,
        "n_samples":n,"n_events":2,
    }
    meta_path.write_text(json.dumps(meta))
    return csv_path, events_path, meta_path

def test_mne_ready_csv_uses_metadata_and_events(tmp_path):
    csv_path, _, _ = make_bundle(tmp_path)
    raw=load_eeg(csv_path)
    desc=json.loads(raw.info["description"])
    assert raw.info["sfreq"] == 256.0
    assert raw.ch_names == ["TP9","AF7","AF8","TP10"]
    assert list(raw.annotations.description) == ["AUTO: Eyes closed","MANUAL: task_start"]
    assert desc["source"] == "ANR Muse EEG MNE-ready"
    assert desc["timing_source"] == "sample_index / sampling_frequency_hz"

def test_mne_ready_zip_loads_directly(tmp_path):
    csv_path, events_path, meta_path = make_bundle(tmp_path)
    zip_path=tmp_path/"session_MNE_READY.zip"
    with zipfile.ZipFile(zip_path,"w") as z:
        for p in (csv_path,events_path,meta_path):
            z.write(p,p.name)
    raw=load_eeg(zip_path)
    assert raw.n_times == 512
    assert len(raw.annotations) == 2

def test_mne_ready_rejects_inconsistent_time_s(tmp_path):
    csv_path, _, _ = make_bundle(tmp_path,bad_time=True)
    with pytest.raises(ValueError, match="time_s"):
        load_eeg(csv_path)


def test_mne_ready_csv_without_events_tsv_falls_back_to_csv_markers(tmp_path):
    csv_path, events_path, meta_path = make_bundle(tmp_path)
    events_path.unlink()

    df = pd.read_csv(csv_path)
    df["event_marker"] = df["event_marker"].astype(object)
    df.loc[128, "event_marker"] = "MANUAL: fallback"
    df.to_csv(csv_path, index=False)

    meta = json.loads(meta_path.read_text())
    meta["events_file"] = "missing_events.tsv"
    meta_path.write_text(json.dumps(meta))

    raw = load_eeg(csv_path)

    assert list(raw.annotations.description) == [
        "MANUAL: fallback"
    ]