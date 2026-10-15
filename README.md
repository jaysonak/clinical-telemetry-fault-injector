# Clinical Telemetry Fault Injector & DSP Parity Framework

An open-source Software Development Engineer in Test (SDET) verification framework designed to test and safeguard wireless medical patient-monitoring software against hospital network failures.

![Telemetry Recovery Demo](assets/eeg_recovery_demo.png)

---

## 1. Plain-English Overview (Why This Matters for Patient Safety)

In modern hospitals, patients hooked up to brain (EEG) or muscle (EMG) monitors often wear wireless sensors that transmit live health data over hospital Wi-Fi to a central nursing station. 

**The Problem:** Hospital Wi-Fi is crowded and imperfect. When a patient moves down a hallway or medical machinery causes electrical interference, small chunks of wireless data get dropped or distorted. Traditional software testing only tests medical apps under "perfect" lab conditions. When real-world Wi-Fi dropouts hit unprepared software, the clinical screen can freeze, crash, or trigger a false emergency alarm.

**How This Framework Solves It:** 
Instead of waiting for software to fail on a real patient, this framework acts as an **automated crash-test simulator for medical software**:
1. **Generates a Safe, Synthetic Brainwave (`src/generator.py`):** Uses pure math to draw a realistic 256 Hz human brainwave (Panel 1 in the chart above) so zero real patient data is ever exposed.
2. **Simulates Hospital Wi-Fi Failures (`src/injector.py`):** Intentionally damages that clean brainwave with missing Wi-Fi packets and sudden 50-volt electrical spikes (Panel 2 in the chart above).
3. **Repairs and Verifies the Signal (`src/dsp_processor.py`):** Reconstructs the missing pieces, filters out the dangerous voltage spikes, and proves mathematically—both in wave shape (RMSE) and brainwave frequency (FFT)—that the recovered signal matches the patient's true baseline (Panel 3 in the chart above).
4. **Blocks Unsafe Software Automatically (`tests/` & `VALIDATION_REPORT.md`):** Runs 6 automated safety gates on every code update. If the software fails to handle a blackout or distorts the patient's brainwave, the release is automatically blocked.

---

## 2. Repository Architecture

* `src/generator.py` — Synthesizes a 256 Hz healthy 10 Hz Alpha brainwave with realistic room noise.
* `src/injector.py` — Injects contiguous Wi-Fi packet loss (`NaN`), $\pm 50\text{ V}$ hardware spikes, and timing jitter.
* `src/dsp_processor.py` — Performs linear packet interpolation, voltage spike clamping, signal smoothing, and Fast Fourier Transform (FFT) frequency verification.
* `src/visualizer.py` — Generates the 3-panel clinical waveform recovery diagram (`assets/eeg_recovery_demo.png`).
* `src/audit_reporter.py` — Automatically generates an FDA/IEC 62304-aligned verification certificate (`VALIDATION_REPORT.md`).
* `tests/` — Automated `pytest` release-gating suite enforcing time-domain, frequency-domain, and fail-safe blackout rules.

---

## 3. Automated Release-Gating Matrix

Every code change is verified against six strict mathematical safety gates:

| Release Gate | Test Case | Hospital Fault Simulated | Patient Safety Acceptance Criteria |
| :--- | :--- | :--- | :--- |
| **Gate 1** | `test_clean_signal_numerical_parity` | Normal 256 Hz wireless stream | Zero `NaN` gaps; sample count preserved; RMSE $< 0.25$ |
| **Gate 2** | `test_corrupted_stream_recovery_parity` | 10% Wi-Fi packet loss + $\pm 50\text{ V}$ spikes | 100% packet interpolation; spikes clamped $\le 5.0\text{ V}$; RMSE $< 0.65$ |
| **Gate 3** | `test_total_blackout_raises_clinical_alert` | 100% Wi-Fi disconnection | Explicitly raises a `ValueError` clinical alarm (never draws a silent flatline) |
| **Gate 4** | `test_invalid_smoothing_window_rejected` | Corrupted filter configuration | Immediately rejects invalid DSP parameters before processing |
| **Gate 5** | `test_latency_jitter_bounds` | Delayed packet arrival times | Confirms network timing jitter stays strictly within $\pm 5.0\text{ ms}$ |
| **Gate 6** | `test_spectral_frequency_parity_preserved` | 15% packet loss + 50V spikes | Fast Fourier Transform (FFT) proves the 10.0 Hz brainwave frequency is preserved ($\pm 0.5\text{ Hz}$) |

---

## 4. Quick Start & Verification Commands

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Generate the 3-panel visual EEG recovery chart
python src/visualizer.py

# 3. Generate the formal IEC 62304 Verification Audit Report (VALIDATION_REPORT.md)
python src/audit_reporter.py

# 4. Run the 6 automated pytest release gates
python -m pytest -v