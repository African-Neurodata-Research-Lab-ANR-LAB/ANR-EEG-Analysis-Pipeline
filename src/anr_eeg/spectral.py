"""Power spectral density and EEG band-power features."""

from __future__ import annotations

import mne
import numpy as np
import pandas as pd

BANDS = {
    "delta": (1.0, 4.0),
    "theta": (4.0, 8.0),
    "alpha": (8.0, 13.0),
    "beta": (13.0, 30.0),
}


def _require_duration(raw: mne.io.BaseRaw, minimum_s: float = 2.0) -> None:
    duration = raw.n_times / raw.info["sfreq"]
    if duration < minimum_s:
        raise ValueError(f"Recording is too short for PSD analysis; need at least {minimum_s:g} seconds")


def compute_psd(raw: mne.io.BaseRaw, *, fmin: float = 1.0, fmax: float = 40.0):
    """Compute Welch PSD for EEG channels."""
    _require_duration(raw)
    nyquist = raw.info["sfreq"] / 2.0
    if fmax >= nyquist:
        fmax = nyquist - 1e-6
    return raw.compute_psd(
        method="welch",
        fmin=fmin,
        fmax=fmax,
        picks="eeg",
        verbose=False,
    )


def compute_band_power(raw: mne.io.BaseRaw) -> pd.DataFrame:
    """Compute relative delta/theta/alpha/beta power per EEG channel."""
    spectrum = compute_psd(raw, fmin=1.0, fmax=30.0)
    psd, freqs = spectrum.get_data(return_freqs=True)
    totals = np.trapezoid(psd, freqs, axis=1)
    totals = np.where(totals <= 0, np.nan, totals)
    result: dict[str, np.ndarray] = {}
    for name, (lo, hi) in BANDS.items():
        mask = (freqs >= lo) & (freqs <= hi)
        result[name] = np.trapezoid(psd[:, mask], freqs[mask], axis=1) / totals
    frame = pd.DataFrame(result, index=spectrum.ch_names)
    frame.index.name = "channel"
    return frame
