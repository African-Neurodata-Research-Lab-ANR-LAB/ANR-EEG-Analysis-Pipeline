"""EEG input helpers for ANR and standard MNE-supported formats."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import mne
import numpy as np
import pandas as pd

from .events import markers_to_annotations

MUSE_COLUMNS = {
    "TP9_uV": "TP9",
    "AF7_uV": "AF7",
    "AF8_uV": "AF8",
    "TP10_uV": "TP10",
}

MUSE_DEFAULT_SFREQ = 256.0


def _timestamp_seconds(df: pd.DataFrame) -> tuple[np.ndarray | None, str | None]:
    """Return relative seconds and the first fully usable timestamp source."""
    if "timestamp_ms" in df.columns:
        values = pd.to_numeric(
            df["timestamp_ms"], errors="coerce"
        ).to_numpy(dtype=float)

        if len(values) >= 2 and np.isfinite(values).all():
            return (values - values[0]) / 1000.0, "timestamp_ms"

    if "iso_time" in df.columns:
        parsed = pd.to_datetime(
            df["iso_time"], errors="coerce", utc=True
        )

        if len(parsed) >= 2 and not parsed.isna().any():
            ns = parsed.astype("int64").to_numpy(dtype=np.int64)
            return (ns - ns[0]) / 1e9, "iso_time"

    return None, None


def _valid_consecutive_sample_index(df: pd.DataFrame) -> bool:
    """Return True when sample_index is finite, increasing, and gap-free."""
    if "sample_index" not in df.columns:
        return False

    values = pd.to_numeric(
        df["sample_index"], errors="coerce"
    ).to_numpy(dtype=float)

    if len(values) < 2 or not np.isfinite(values).all():
        return False

    diffs = np.diff(values)
    return bool(np.allclose(diffs, 1.0, rtol=0.0, atol=1e-9))


def _estimate_sfreq(
    df: pd.DataFrame,
) -> tuple[float, dict[str, Any]]:
    seconds, timing_source = _timestamp_seconds(df)

    if seconds is None:
        if _valid_consecutive_sample_index(df):
            return MUSE_DEFAULT_SFREQ, {
                "estimated_sfreq_hz": MUSE_DEFAULT_SFREQ,
                "sampling_rate_source": "muse_default",
                "timing_source": "sample_index",
                "timing_note": (
                    "timestamp_ms/iso_time unavailable; used consecutive "
                    "sample_index with the Muse default sampling rate of 256 Hz"
                ),
            }

        raise ValueError(
            "ANR Muse CSV has no usable timestamp_ms/iso_time values and no "
            "consecutive sample_index fallback. Provide a valid time column or "
            "call load_eeg(..., sfreq=<known_sampling_rate>)."
        )

    diffs = np.diff(seconds)
    positive = diffs[np.isfinite(diffs) & (diffs > 0)]

    if len(positive) < 2:
        raise ValueError(
            "Unable to estimate sampling rate from timestamps"
        )

    median_dt = float(np.median(positive))
    sfreq = 1.0 / median_dt

    if not np.isfinite(sfreq) or sfreq < 10 or sfreq > 5000:
        raise ValueError(
            f"Implausible sampling rate estimated from timestamps: "
            f"{sfreq!r} Hz"
        )

    if (
        abs(sfreq - MUSE_DEFAULT_SFREQ) / MUSE_DEFAULT_SFREQ
        <= 0.01
    ):
        sfreq = MUSE_DEFAULT_SFREQ

    jitter = float(
        np.median(np.abs(positive - median_dt))
    )

    metadata = {
        "estimated_sfreq_hz": sfreq,
        "sampling_rate_source": "timestamps",
        "timing_source": timing_source,
        "median_sample_interval_s": median_dt,
        "median_absolute_interval_jitter_s": jitter,
    }

    return sfreq, metadata


def _load_anr_muse_csv(
    path: str | Path,
    sfreq: float | None = None,
) -> mne.io.RawArray:
    path = Path(path)
    df = pd.read_csv(path)

    missing = [
        name
        for name in MUSE_COLUMNS
        if name not in df.columns
    ]

    if missing:
        raise ValueError(
            "Missing required ANR Muse EEG column(s): "
            + ", ".join(missing)
        )

    timing_meta: dict[str, Any] = {}

    if sfreq is None:
        sfreq, timing_meta = _estimate_sfreq(df)
    else:
        sfreq = float(sfreq)

        if not np.isfinite(sfreq) or sfreq <= 0:
            raise ValueError(
                "sfreq must be a positive finite number"
            )

        timing_meta = {
            "estimated_sfreq_hz": sfreq,
            "sampling_rate_source": "user_supplied",
            "timing_source": (
                "sample_index"
                if _valid_consecutive_sample_index(df)
                else "user_supplied_sfreq"
            ),
        }

    values_uv = df[list(MUSE_COLUMNS)].apply(
        pd.to_numeric,
        errors="coerce",
    )

    if values_uv.isna().any().any():
        raise ValueError(
            "ANR Muse EEG columns contain non-numeric or missing values"
        )

    data_v = values_uv.to_numpy(dtype=float).T * 1e-6

    info = mne.create_info(
        ch_names=list(MUSE_COLUMNS.values()),
        sfreq=sfreq,
        ch_types=["eeg"] * len(MUSE_COLUMNS),
    )

    raw = mne.io.RawArray(
        data_v,
        info,
        verbose=False,
    )

    annotations = markers_to_annotations(df, sfreq)
    raw.set_annotations(annotations)

    description = {
        "source": "ANR Muse EEG Recorder CSV",
        "source_file": path.name,
        "channel_units_input": "microvolts",
        "channel_units_mne": "volts",
        "event_count": len(annotations),
        **timing_meta,
    }

    raw.info["description"] = json.dumps(
        description,
        sort_keys=True,
    )

    return raw


def load_eeg(
    path: str | Path | None = None,
    *,
    sfreq: float | None = None,
    format: str | None = None,
    bids_path: object | None = None,
) -> mne.io.BaseRaw:
    """Load EEG into an MNE Raw object.

    ANR Muse CSV is the primary format. EDF/BDF, FIF, BrainVision,
    and BIDS are delegated to MNE/MNE-BIDS readers.
    """
    fmt = format.lower() if format else None

    if fmt == "bids":
        if bids_path is None:
            raise ValueError(
                "bids_path is required when format='bids'"
            )

        try:
            from mne_bids import read_raw_bids
        except ImportError as exc:
            raise ImportError(
                "BIDS loading requires mne-bids"
            ) from exc

        return read_raw_bids(
            bids_path=bids_path,
            verbose=False,
        ).load_data()

    if path is None:
        raise ValueError(
            "path is required unless loading from BIDS"
        )

    path = Path(path)
    suffix = path.suffix.lower()

    if (
        fmt in {"anr", "muse", "csv"}
        or (fmt is None and suffix == ".csv")
    ):
        return _load_anr_muse_csv(
            path,
            sfreq=sfreq,
        )

    if (
        fmt in {"edf", "bdf"}
        or (fmt is None and suffix in {".edf", ".bdf"})
    ):
        return mne.io.read_raw_edf(
            path,
            preload=True,
            verbose=False,
        )

    if fmt == "fif" or (
        fmt is None and suffix == ".fif"
    ):
        return mne.io.read_raw_fif(
            path,
            preload=True,
            verbose=False,
        )

    if (
        fmt in {"brainvision", "vhdr"}
        or (fmt is None and suffix == ".vhdr")
    ):
        return mne.io.read_raw_brainvision(
            path,
            preload=True,
            verbose=False,
        )

    raise ValueError(
        f"Unsupported EEG format for {path.name!r}"
    )
