import json
import pandas as pd
from anr_eeg import load_eeg, run_qc, compute_band_power, export_results


def test_export_results_writes_parseable_outputs(muse_csv, tmp_path):
    raw = load_eeg(muse_csv)
    qc = run_qc(raw)
    bands = compute_band_power(raw)
    paths = export_results(raw, qc, bands, tmp_path, prefix="test")
    for p in paths.values():
        assert p.exists()
    json.loads(paths["qc_json"].read_text())
    json.loads(paths["summary_json"].read_text())
    parsed = pd.read_csv(paths["band_power_csv"])
    assert set(parsed["channel"]) == {"TP9", "AF7", "AF8", "TP10"}
