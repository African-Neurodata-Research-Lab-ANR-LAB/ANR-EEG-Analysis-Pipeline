"""Technical acquisition quality-control summaries."""

from __future__ import annotations

import numpy as np
import mne


def run_qc(raw: mne.io.BaseRaw) -> dict:
    """Return a JSON-serializable technical QC summary for EEG acquisition."""
    picks = mne.pick_types(raw.info, eeg=True, exclude=[])
    data = raw.get_data(picks=picks)
    channels: dict[str, dict] = {}
    any_fail = False
    any_review = False

    for row, pick in zip(data, picks):
        name = raw.ch_names[pick]
        finite = np.isfinite(row)
        finite_count = int(finite.sum())
        if finite_count == 0:
            sd_uv = None
            p2p_uv = None
            flat = True
            high_amplitude = False
            any_fail = True
        else:
            values_uv = row[finite] * 1e6
            sd_uv = float(np.std(values_uv))
            p2p_uv = float(np.ptp(values_uv))
            flat = sd_uv < 0.1
            high_amplitude = p2p_uv > 1000.0
            any_fail = any_fail or flat or finite_count != len(row)
            any_review = any_review or high_amplitude

        channels[name] = {
            "finite_samples": finite_count,
            "total_samples": int(len(row)),
            "std_uv": sd_uv,
            "peak_to_peak_uv": p2p_uv,
            "flat": bool(flat),
            "high_amplitude_review": bool(high_amplitude),
        }

    duration = float(raw.n_times / raw.info["sfreq"]) if raw.n_times else 0.0
    if duration < 10.0:
        any_review = True
    status = "fail" if any_fail else "review" if any_review else "pass"

    return {
        "status": status,
        "channel_count": int(len(picks)),
        "sampling_frequency_hz": float(raw.info["sfreq"]),
        "duration_seconds": duration,
        "sample_count": int(raw.n_times),
        "annotation_count": int(len(raw.annotations)),
        "non_finite_sample_count": int((~np.isfinite(data)).sum()),
        "channels": channels,
        "interpretation": "Technical acquisition quality only; not clinical EEG interpretation.",
    }
