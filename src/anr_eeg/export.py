"""Export standardized ANR EEG analysis outputs."""

from __future__ import annotations

import json
from pathlib import Path

import mne
import pandas as pd


def export_results(
    raw: mne.io.BaseRaw,
    qc: dict,
    band_power: pd.DataFrame,
    output_dir: str | Path,
    *,
    prefix: str = "anr_eeg",
) -> dict[str, Path]:
    """Write cleaned FIF, QC JSON, band-power CSV and summary JSON."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "raw_fif": output_dir / f"{prefix}_clean_raw.fif",
        "qc_json": output_dir / f"{prefix}_qc.json",
        "band_power_csv": output_dir / f"{prefix}_band_power.csv",
        "summary_json": output_dir / f"{prefix}_summary.json",
    }
    raw.save(paths["raw_fif"], overwrite=True, verbose=False)
    paths["qc_json"].write_text(json.dumps(qc, indent=2, sort_keys=True), encoding="utf-8")
    band_power.to_csv(paths["band_power_csv"], index_label="channel")
    summary = {
        "pipeline": "ANR-EEG-Analysis-Pipeline",
        "pipeline_version": "0.1.0",
        "mne_version": mne.__version__,
        "sampling_frequency_hz": float(raw.info["sfreq"]),
        "channels": list(raw.ch_names),
        "duration_seconds": float(raw.n_times / raw.info["sfreq"]),
        "qc_status": qc.get("status"),
        "outputs": {key: path.name for key, path in paths.items() if key != "summary_json"},
        "research_use_only": True,
    }
    paths["summary_json"].write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    return paths
