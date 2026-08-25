# Loading ANR MNE-Ready Recordings

The preferred input for the ANR EEG Analysis Pipeline is the **MNE-ready ZIP** exported by the ANR Muse EEG Recorder.

## Recommended: upload the ZIP

In Python:

```python
from anr_eeg import load_eeg

raw = load_eeg("ANR_ANR-001_..._MNE_READY.zip")
```

The loader automatically:

1. extracts the package into a temporary working directory;
2. finds the ANR EEG metadata JSON;
3. reads the declared sampling frequency;
4. validates `sample_index`;
5. verifies `time_s = sample_index / sampling_frequency_hz`;
6. converts TP9/AF7/AF8/TP10 from microvolts to volts;
7. creates an MNE `RawArray`;
8. loads `events.tsv` as MNE annotations.

The temporary extracted files are removed after loading because the MNE object is preloaded in memory.

## Alternative: upload the three extracted files

Upload these files together into the same directory:

```text
<prefix>_raw_eeg.csv
<prefix>_events.tsv
<prefix>_eeg_metadata.json
```

Then pass only the raw EEG CSV to `load_eeg()`:

```python
raw = load_eeg("<prefix>_raw_eeg.csv")
```

The loader detects the companion metadata and events files automatically.

## Legacy CSV compatibility

Older ANR Muse CSV recordings remain supported.

If no companion MNE-ready metadata is found, the loader uses the legacy CSV workflow, including timestamp estimation and the validated Muse `sample_index` fallback.

## Validation behavior

The MNE-ready loader stops with an error rather than silently guessing when:

- the metadata sampling rate is invalid;
- required Muse channels are missing;
- `sample_index` is missing, non-consecutive, or does not start at zero;
- `time_s` disagrees with `sample_index / sampling_frequency_hz`;
- metadata `n_samples` disagrees with the EEG CSV;
- an event has an invalid time;
- the ZIP contains zero or multiple valid ANR metadata files.

## Events

When `events.tsv` is present it is the authoritative event source.

Required columns:

```text
onset
duration
description
```

The optional `source` column may contain values such as `auto` or `manual`.

If no events TSV exists, the loader can fall back to the `event_marker` column in the raw CSV.

## Saving native MNE FIF

After loading:

```python
raw.save("ANR_session_raw.fif", overwrite=True)
```

The FIF file is the native MNE representation used for subsequent analysis.

## Research-use statement

ANR MNE-ready input validation and technical QC support research workflows. They do not provide clinical EEG interpretation or diagnosis.
