import numpy as np
from src.generator import generate_eeg_signal
from src.injector import inject_packet_loss, inject_anomalous_spikes
from src.dsp_processor import process_telemetry_stream


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