"""EEG input helpers for ANR and standard MNE-supported formats."""

from __future__ import annotations

import json
import tempfile
import zipfile
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
ANR_MNE_READY_FORMAT = "ANR Muse EEG MNE-ready"


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


def _validate_muse_values(df: pd.DataFrame) -> np.ndarray:
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

    values_uv = df[list(MUSE_COLUMNS)].apply(
        pd.to_numeric,
        errors="coerce",
    )

    if values_uv.isna().any().any():
        raise ValueError(
            "ANR Muse EEG columns contain non-numeric or missing values"
        )

    return values_uv.to_numpy(dtype=float)


def _make_raw(values_uv: np.ndarray, sfreq: float) -> mne.io.RawArray:
    data_v = values_uv.T * 1e-6
    info = mne.create_info(
        ch_names=list(MUSE_COLUMNS.values()),
        sfreq=sfreq,
        ch_types=["eeg"] * len(MUSE_COLUMNS),
    )
    return mne.io.RawArray(data_v, info, verbose=False)


def _load_anr_muse_csv(
    path: str | Path,
    sfreq: float | None = None,
) -> mne.io.RawArray:
    """Load legacy/single-file ANR Muse CSV recordings."""
    path = Path(path)
    df = pd.read_csv(path)
    values_uv = _validate_muse_values(df)

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

    raw = _make_raw(values_uv, sfreq)
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


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(
            f"Unable to read ANR EEG metadata file {path.name!r}"
        ) from exc
    if not isinstance(value, dict):
        raise ValueError("ANR EEG metadata must be a JSON object")
    return value


def _companion_metadata_path(csv_path: Path) -> Path | None:
    if csv_path.name.endswith("_raw_eeg.csv"):
        candidate = csv_path.with_name(
            csv_path.name[:-len("_raw_eeg.csv")] + "_eeg_metadata.json"
        )
        if candidate.exists():
            return candidate

    for candidate in sorted(csv_path.parent.glob("*_eeg_metadata.json")):
        try:
            metadata = _read_json(candidate)
        except ValueError:
            continue
        if (
            metadata.get("format") == ANR_MNE_READY_FORMAT
            and Path(str(metadata.get("eeg_file", ""))).name == csv_path.name
        ):
            return candidate
    return None


def _resolve_declared_file(
    directory: Path,
    declared_name: object,
    fallback_pattern: str,
) -> Path | None:
    if declared_name:
        declared = directory / Path(str(declared_name)).name
        if declared.exists():
            return declared
    matches = sorted(directory.glob(fallback_pattern))
    if len(matches) == 1:
        return matches[0]
    return None


def _annotations_from_events_tsv(
    path: Path,
    recording_duration_s: float,
) -> mne.Annotations:
    events = pd.read_csv(path, sep="\t")
    required = {"onset", "duration", "description"}
    missing = sorted(required.difference(events.columns))
    if missing:
        raise ValueError(
            "ANR events.tsv missing required column(s): "
            + ", ".join(missing)
        )

    onset = pd.to_numeric(events["onset"], errors="coerce")
    duration = pd.to_numeric(events["duration"], errors="coerce")
    description = events["description"].fillna("").astype(str).str.strip()

    if onset.isna().any() or duration.isna().any():
        raise ValueError("ANR events.tsv contains invalid onset/duration values")
    if (onset < 0).any() or (duration < 0).any():
        raise ValueError("ANR events.tsv onset/duration cannot be negative")
    if (description == "").any():
        raise ValueError("ANR events.tsv contains an empty description")
    if (onset > recording_duration_s + 1e-9).any():
        raise ValueError("ANR events.tsv contains an event beyond the EEG duration")

    return mne.Annotations(
        onset=onset.to_numpy(dtype=float),
        duration=duration.to_numpy(dtype=float),
        description=description.tolist(),
    )


def _load_anr_mne_ready_csv(
    csv_path: Path,
    metadata_path: Path,
    *,
    events_path: Path | None = None,
    bundle_name: str | None = None,
) -> mne.io.RawArray:
    metadata = _read_json(metadata_path)

    if metadata.get("format") != ANR_MNE_READY_FORMAT:
        raise ValueError(
            f"Unsupported ANR metadata format: {metadata.get('format')!r}"
        )

    try:
        sfreq = float(metadata["sampling_frequency_hz"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(
            "ANR MNE-ready metadata requires sampling_frequency_hz"
        ) from exc

    if not np.isfinite(sfreq) or sfreq <= 0:
        raise ValueError(
            "sampling_frequency_hz must be a positive finite number"
        )

    df = pd.read_csv(csv_path)
    values_uv = _validate_muse_values(df)

    if "sample_index" not in df.columns:
        raise ValueError(
            "ANR MNE-ready CSV requires sample_index"
        )

    sample_index = pd.to_numeric(
        df["sample_index"], errors="coerce"
    ).to_numpy(dtype=float)

    if (
        len(sample_index) < 1
        or not np.isfinite(sample_index).all()
        or sample_index[0] != 0
        or (
            len(sample_index) > 1
            and not np.allclose(
                np.diff(sample_index),
                1.0,
                rtol=0.0,
                atol=1e-9,
            )
        )
    ):
        raise ValueError(
            "ANR MNE-ready CSV requires sample_index starting at 0 "
            "and increasing by exactly 1"
        )

    expected_time = sample_index / sfreq
    if "time_s" in df.columns:
        time_s = pd.to_numeric(
            df["time_s"], errors="coerce"
        ).to_numpy(dtype=float)
        if (
            not np.isfinite(time_s).all()
            or not np.allclose(
                time_s,
                expected_time,
                rtol=0.0,
                atol=5e-9,
            )
        ):
            raise ValueError(
                "ANR MNE-ready CSV time_s is inconsistent with "
                "sample_index / sampling_frequency_hz"
            )

    if metadata.get("n_samples") is not None:
        if int(metadata["n_samples"]) != len(df):
            raise ValueError(
                "ANR metadata n_samples does not match the EEG CSV"
            )

    declared_channels = metadata.get("channel_names")
    if declared_channels is not None:
        if list(declared_channels) != list(MUSE_COLUMNS.values()):
            raise ValueError(
                "ANR metadata channel_names do not match the supported "
                "Muse channel order TP9, AF7, AF8, TP10"
            )

    raw = _make_raw(values_uv, sfreq)
    recording_duration_s = raw.n_times / sfreq

    if events_path is None:
        events_path = _resolve_declared_file(
            csv_path.parent,
            metadata.get("events_file"),
            "*_events.tsv",
        )

    if events_path is not None and events_path.exists():
        annotations = _annotations_from_events_tsv(
            events_path,
            recording_duration_s,
        )
    else:
        annotations = markers_to_annotations(df, sfreq)

    raw.set_annotations(annotations)

    description = {
        "source": ANR_MNE_READY_FORMAT,
        "source_file": csv_path.name,
        "metadata_file": metadata_path.name,
        "events_file": events_path.name if events_path else None,
        "bundle_file": bundle_name,
        "sampling_rate_source": "metadata",
        "timing_source": metadata.get(
            "mne_time_source",
            "sample_index / sampling_frequency_hz",
        ),
        "channel_units_input": metadata.get("units", "microvolts"),
        "channel_units_mne": "volts",
        "event_count": len(annotations),
        "format_version": metadata.get("format_version"),
        "session_code": metadata.get("session_code"),
        "protocol": metadata.get("protocol"),
        "wall_clock_duration_seconds": metadata.get(
            "wall_clock_duration_seconds",
            metadata.get("recording_duration_seconds"),
        ),
        "eeg_duration_seconds": metadata.get(
            "eeg_duration_seconds",
            recording_duration_s,
        ),
    }

    raw.info["description"] = json.dumps(
        description,
        sort_keys=True,
    )
    return raw


def _safe_extract_zip(zip_path: Path, target: Path) -> None:
    with zipfile.ZipFile(zip_path) as archive:
        for member in archive.infolist():
            member_path = Path(member.filename)
            if member_path.is_absolute() or ".." in member_path.parts:
                raise ValueError(
                    "ANR MNE-ready ZIP contains an unsafe path"
                )
        archive.extractall(target)


def _load_anr_mne_ready_zip(path: Path) -> mne.io.RawArray:
    try:
        with tempfile.TemporaryDirectory(prefix="anr_eeg_") as tmp:
            tmp_dir = Path(tmp)
            _safe_extract_zip(path, tmp_dir)

            metadata_candidates = sorted(
                tmp_dir.rglob("*_eeg_metadata.json")
            )
            if not metadata_candidates:
                metadata_candidates = sorted(
                    tmp_dir.rglob("*.json")
                )

            valid: list[tuple[Path, dict[str, Any]]] = []
            for candidate in metadata_candidates:
                try:
                    metadata = _read_json(candidate)
                except ValueError:
                    continue
                if metadata.get("format") == ANR_MNE_READY_FORMAT:
                    valid.append((candidate, metadata))

            if len(valid) != 1:
                raise ValueError(
                    "ANR MNE-ready ZIP must contain exactly one valid "
                    "*_eeg_metadata.json file"
                )

            metadata_path, metadata = valid[0]
            directory = metadata_path.parent
            csv_path = _resolve_declared_file(
                directory,
                metadata.get("eeg_file"),
                "*_raw_eeg.csv",
            )
            if csv_path is None:
                # Support ZIPs where files are in a single nested directory
                csv_matches = sorted(
                    tmp_dir.rglob("*_raw_eeg.csv")
                )
                if len(csv_matches) == 1:
                    csv_path = csv_matches[0]

            if csv_path is None:
                raise ValueError(
                    "ANR MNE-ready ZIP does not contain the declared raw EEG CSV"
                )

            events_path = _resolve_declared_file(
                csv_path.parent,
                metadata.get("events_file"),
                "*_events.tsv",
            )
            if events_path is None:
                event_matches = sorted(
                    tmp_dir.rglob("*_events.tsv")
                )
                if len(event_matches) == 1:
                    events_path = event_matches[0]

            return _load_anr_mne_ready_csv(
                csv_path,
                metadata_path,
                events_path=events_path,
                bundle_name=path.name,
            )
    except zipfile.BadZipFile as exc:
        raise ValueError(
            f"Invalid ZIP file: {path.name!r}"
        ) from exc


def load_eeg(
    path: str | Path | None = None,
    *,
    sfreq: float | None = None,
    format: str | None = None,
    bids_path: object | None = None,
) -> mne.io.BaseRaw:
    """Load EEG into an MNE Raw object.

    Preferred ANR input is the MNE-ready ZIP exported by the ANR Muse EEG
    Recorder. Extracted MNE-ready raw CSV files are also detected through
    their companion metadata JSON and events TSV.

    Legacy ANR Muse CSV, EDF/BDF, FIF, BrainVision, and BIDS remain supported.
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
        fmt in {"anr_bundle", "mne_ready", "zip"}
        or (fmt is None and suffix == ".zip")
    ):
        return _load_anr_mne_ready_zip(path)

    if (
        fmt in {"anr", "muse", "csv"}
        or (fmt is None and suffix == ".csv")
    ):
        metadata_path = _companion_metadata_path(path)
        if metadata_path is not None:
            return _load_anr_mne_ready_csv(
                path,
                metadata_path,
            )
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
