"""
Automated Numerical & Spectral Parity Release Gates
===================================================
These automated pytest assertions act as release-gating checkpoints.
If a software update causes the recovered patient waveform to drift away from
the true physiological baseline—either in voltage (RMSE) or brainwave frequency (Hz)—
the test suite automatically blocks the release.
"""

import numpy as np
from src.generator import generate_eeg_signal
from src.injector import inject_packet_loss, inject_anomalous_spikes
from src.dsp_processor import process_telemetry_stream, compute_dominant_frequency


def test_clean_signal_numerical_parity():
    """
    Release Gate 1: Verifies that an uncorrupted synthetic EEG stream passes
    through the DSP pipeline while maintaining tight mathematical parity.
    """
    np.random.seed(42)
    _, clean_signal = generate_eeg_signal(duration_seconds=4, sample_rate=256)

    processed_signal = process_telemetry_stream(clean_signal, smoothing_window=5)

    assert not np.any(np.isnan(processed_signal)), "Processed signal contains unexpected NaN values."
    assert len(processed_signal) == len(clean_signal), "Sample count mismatch after DSP processing."

    rmse = np.sqrt(np.mean((clean_signal - processed_signal) ** 2))
    assert rmse < 0.25, f"Clean signal parity failed: RMSE ({rmse:.4f}) exceeded 0.25 threshold."


def test_corrupted_stream_recovery_parity():
    """
    Release Gate 2: Verifies that a telemetry stream degraded by 10% Wi-Fi packet
    loss and 50V hardware spikes is reconstructed within diagnostic tolerances.
    """
    np.random.seed(42)
    _, clean_signal = generate_eeg_signal(duration_seconds=4, sample_rate=256)

    corrupted = inject_packet_loss(clean_signal, drop_rate=0.10, packet_size=16)
    corrupted = inject_anomalous_spikes(corrupted, spike_probability=0.01, spike_magnitude=50.0)

    recovered = process_telemetry_stream(corrupted, max_voltage=5.0, smoothing_window=5)

    # 1. Zero NaN dropouts allowed in downstream clinical graphing
    assert np.isnan(recovered).sum() == 0, "Failed to interpolate all dropped packets."

    # 2. All 50V hardware spikes must be suppressed below the 5.0V physiological ceiling
    assert np.max(np.abs(recovered)) <= 5.0, "Hardware voltage spikes leaked past DSP suppression."

    # 3. Reconstructed waveform must closely track the original baseline signal
    rmse = np.sqrt(np.mean((clean_signal - recovered) ** 2))
    assert rmse < 0.65, f"Recovered signal drifted out of diagnostic parity: RMSE={rmse:.4f}"


def test_spectral_frequency_parity_preserved():
    """
    Release Gate 6 (FFT Spectral Gate): Proves that interpolating across dropped
    Wi-Fi packets does not alter the patient's dominant 10.0 Hz Alpha brainwave
    frequency, preventing false-positive diagnostic classifications.
    """
    np.random.seed(42)
    target_hz = 10.0
    _, clean_signal = generate_eeg_signal(duration_seconds=4, sample_rate=256, frequency=target_hz)

    # Degrade the signal with 15% packet loss and hardware spikes
    corrupted = inject_packet_loss(clean_signal, drop_rate=0.15, packet_size=16)
    corrupted = inject_anomalous_spikes(corrupted, spike_probability=0.015, spike_magnitude=50.0)

    recovered = process_telemetry_stream(corrupted)
    recovered_hz = compute_dominant_frequency(recovered, sample_rate=256)

    # Dominant frequency must remain within +/- 0.5 Hz of the true 10.0 Hz signal
    assert abs(recovered_hz - target_hz) <= 0.5, (
        f"Spectral distortion detected! Expected {target_hz} Hz, got {recovered_hz} Hz."
    )