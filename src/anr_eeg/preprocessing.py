"""Standardized EEG preprocessing built on MNE-Python."""

from __future__ import annotations

import numbers
import mne


def preprocess(
    raw: mne.io.BaseRaw,
    *,
    l_freq: float | None = 1.0,
    h_freq: float | None = 40.0,
    notch: float | None = 50.0,
    reference: str | list[str] | None = None,
) -> mne.io.BaseRaw:
    """Copy and preprocess EEG using notch, band-pass and optional re-reference."""
    clean = raw.copy().load_data()
    nyquist = clean.info["sfreq"] / 2.0
    if h_freq is not None and h_freq >= nyquist:
        raise ValueError(f"h_freq must be below Nyquist frequency ({nyquist:g} Hz)")
    if notch is not None:
        if notch <= 0:
            raise ValueError("notch frequency must be positive")
        if notch < nyquist:
            clean.notch_filter(freqs=[float(notch)], picks="eeg", verbose=False)
    if l_freq is not None or h_freq is not None:
        clean.filter(l_freq=l_freq, h_freq=h_freq, picks="eeg", verbose=False)
    if reference is not None:
        clean.set_eeg_reference(ref_channels=reference, verbose=False)
    return clean
