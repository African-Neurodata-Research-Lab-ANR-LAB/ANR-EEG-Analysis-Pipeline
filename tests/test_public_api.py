def test_public_api_imports():
    import anr_eeg
    expected = {
        "load_eeg", "run_qc", "preprocess", "compute_psd",
        "compute_band_power", "export_results", "make_report",
    }
    assert expected.issubset(set(dir(anr_eeg)))
