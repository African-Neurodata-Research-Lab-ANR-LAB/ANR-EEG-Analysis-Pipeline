from anr_eeg import load_eeg, run_qc, compute_band_power, make_report


def test_make_report_creates_html(muse_csv, tmp_path):
    raw = load_eeg(muse_csv)
    qc = run_qc(raw)
    bands = compute_band_power(raw)
    path = make_report(raw, qc, bands, tmp_path / "report.html")
    assert path.exists()
    text = path.read_text(encoding="utf-8", errors="ignore")
    assert "ANR EEG Analysis Report" in text
    assert "Research use" in text
