from anr_eeg import (
    load_eeg, run_qc, preprocess, compute_band_power, export_results, make_report,
)


def test_anr_muse_csv_end_to_end(muse_csv, tmp_path):
    raw = load_eeg(muse_csv)
    qc = run_qc(raw)
    clean = preprocess(raw, notch=None)
    bands = compute_band_power(clean)
    outputs = export_results(clean, qc, bands, tmp_path)
    report = make_report(clean, qc, bands, tmp_path / "report.html")
    assert qc["channel_count"] == 4
    assert outputs["raw_fif"].exists()
    assert report.exists()
