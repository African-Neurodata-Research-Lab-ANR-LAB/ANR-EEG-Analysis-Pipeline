"""Event marker utilities for ANR EEG recordings."""

from __future__ import annotations

import math

import mne
import pandas as pd


def _clean_marker(value: object) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return ""
    text = str(value).strip()
    return "" if text.lower() == "nan" else text


def markers_to_annotations(df: pd.DataFrame, sfreq: float) -> mne.Annotations:
    """Convert ANR ``event_marker`` rows to deduplicated MNE annotations.

    Adjacent rows containing the same marker text represent one event occurrence.
    """
    if "event_marker" not in df.columns:
        return mne.Annotations([], [], [])

    onsets: list[float] = []
    descriptions: list[str] = []
    previous = ""
    for idx, value in enumerate(df["event_marker"].tolist()):
        marker = _clean_marker(value)
        if marker and marker != previous:
            onsets.append(idx / float(sfreq))
            descriptions.append(marker)
        previous = marker

    return mne.Annotations(onset=onsets, duration=[0.0] * len(onsets), description=descriptions)
