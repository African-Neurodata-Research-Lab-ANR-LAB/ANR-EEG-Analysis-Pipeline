from anr_eeg import load_eeg


def test_adjacent_duplicate_markers_become_one_annotation(muse_csv):
    raw = load_eeg(muse_csv)
    assert len(raw.annotations) == 2
    assert raw.annotations.description[0] == "AUTO: eyes_closed"
    assert abs(raw.annotations.onset[0] - 1.0) < 1 / 256
    assert raw.annotations.description[1] == "MANUAL: task_start"
    assert abs(raw.annotations.onset[1] - 5.0) < 1 / 256
