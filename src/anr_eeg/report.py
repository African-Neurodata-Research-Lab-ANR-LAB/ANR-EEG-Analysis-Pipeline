"""MNE HTML research report generation."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import mne
import pandas as pd

from .spectral import compute_psd


def make_report(
    raw: mne.io.BaseRaw,
    qc: dict,
    band_power: pd.DataFrame,
    output_path: str | Path,
    *,
    title: str = "ANR EEG Analysis Report",
) -> Path:
    """Create an HTML report containing technical EEG research summaries."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    report = mne.Report(title=title, verbose=False)

    metadata_html = (
        f"<h3>Recording metadata</h3>"
        f"<p><b>Channels:</b> {', '.join(raw.ch_names)}<br>"
        f"<b>Sampling frequency:</b> {raw.info['sfreq']:.3f} Hz<br>"
        f"<b>Duration:</b> {raw.n_times / raw.info['sfreq']:.2f} s<br>"
        f"<b>Annotations:</b> {len(raw.annotations)}</p>"
    )
    report.add_html(metadata_html, title="Recording metadata")

    qc_rows = []
    for name, metrics in qc.get("channels", {}).items():
        qc_rows.append({"channel": name, **metrics})
    qc_df = pd.DataFrame(qc_rows)
    qc_html = f"<p><b>Overall technical status:</b> {qc.get('status','unknown')}</p>" + qc_df.to_html(index=False)
    report.add_html(qc_html, title="Technical quality control")

    spectrum = compute_psd(raw, fmin=1.0, fmax=min(40.0, raw.info['sfreq']/2 - 1e-6))
    psd, freqs = spectrum.get_data(return_freqs=True)
    fig, ax = plt.subplots(figsize=(8, 4.5))
    for values, channel in zip(psd, spectrum.ch_names):
        ax.semilogy(freqs, values, label=channel)
    ax.set_xlabel("Frequency (Hz)")
    ax.set_ylabel("Power spectral density")
    ax.set_title("EEG power spectral density")
    ax.legend(loc="best", fontsize="small")
    ax.grid(True, alpha=0.2)
    report.add_figure(fig, title="Power spectral density", caption="Welch PSD for EEG channels")
    plt.close(fig)

    report.add_html(band_power.round(4).to_html(), title="Relative EEG band power")
    annotation_html = "<p>No event annotations.</p>" if len(raw.annotations) == 0 else pd.DataFrame({
        "onset_s": raw.annotations.onset,
        "duration_s": raw.annotations.duration,
        "description": raw.annotations.description,
    }).to_html(index=False)
    report.add_html(annotation_html, title="Event annotations")
    report.add_html(
        "<p><b>Research use only.</b> This report summarizes technical EEG acquisition and research features. "
        "It is not a clinical EEG interpretation and does not diagnose neurological conditions.</p>",
        title="Research-use statement",
    )
    report.save(output_path, overwrite=True, open_browser=False, verbose=False)
    return output_path
