import numpy as np

try:
    from src.generator import generate_eeg_signal
    from src.injector import inject_packet_loss, inject_anomalous_spikes
except ImportError:
    from generator import generate_eeg_signal
    from injector import inject_packet_loss, inject_anomalous_spikes


def interpolate_missing_packets(signal):
    """
    Reconstructs dropped Wi-Fi packets (NaN values) using linear interpolation
    so downstream clinical algorithms do not crash.
    """
    reconstructed = signal.copy().astype(float)
    nan_mask = np.isnan(reconstructed)

    # Return immediately if no packets were dropped
    if not np.any(nan_mask):
        return reconstructed

    # Guard against signals where every single packet was lost
    if np.all(nan_mask):
        raise ValueError("Telemetry stream completely lost: 100% packet drop.")

    valid_indices = np.where(~nan_mask)[0]
    missing_indices = np.where(nan_mask)[0]

    reconstructed[nan_mask] = np.interp(
        missing_indices, valid_indices, reconstructed[valid_indices]
    )
    return reconstructed


def suppress_hardware_spikes(signal, max_physiological_voltage=5.0):
    """
    Detects non-physiological voltage spikes caused by hardware interference
    and marks them as NaN so they can be cleanly interpolated.
    """
    filtered = signal.copy().astype(float)
    spike_mask = np.abs(filtered) > max_physiological_voltage
    filtered[spike_mask] = np.nan
    return interpolate_missing_packets(filtered)


def smooth_signal(signal, window_size=5):
    """
    Applies a causal-style moving average filter to attenuate high-frequency
    baseline noise while preserving diagnostic waveform parity.
    """
    if window_size < 1:
        raise ValueError("Window size must be at least 1.")
    kernel = np.ones(window_size) / window_size
    return np.convolve(signal, kernel, mode="same")


def process_telemetry_stream(raw_corrupted_signal, max_voltage=5.0, smoothing_window=5):
    """
    Full clinical DSP pipeline:
    1. Interpolate dropped network packets (NaNs)
    2. Suppress and interpolate extreme hardware voltage spikes
    3. Smooth high-frequency baseline noise
    """
    step1_packet_recovered = interpolate_missing_packets(raw_corrupted_signal)
    step2_spike_suppressed = suppress_hardware_spikes(
        step1_packet_recovered, max_physiological_voltage=max_voltage
    )
    step3_smoothed = smooth_signal(step2_spike_suppressed, window_size=smoothing_window)
    return step3_smoothed


if __name__ == "__main__":
    # 1. Generate clean baseline signal
    _, clean_signal = generate_eeg_signal(duration_seconds=2)

    # 2. Corrupt the signal with packet loss and hardware spikes
    corrupted = inject_packet_loss(clean_signal, drop_rate=0.15, packet_size=16)
    corrupted = inject_anomalous_spikes(corrupted, spike_probability=0.02)

    # 3. Run the DSP recovery pipeline
    recovered_signal = process_telemetry_stream(corrupted)

    # 4. Verify zero NaNs remain and measure signal recovery error (RMSE)
    remaining_nans = np.isnan(recovered_signal).sum()
    rmse = np.sqrt(np.mean((clean_signal - recovered_signal) ** 2))

    print("--- Clinical DSP Processor Active ---")
    print(f"Remaining NaN Dropouts After DSP: {remaining_nans}")
    print(f"Max Voltage After Spike Suppression: {np.max(np.abs(recovered_signal)):.2f} V")
    print(f"Signal Recovery Root Mean Square Error (RMSE): {rmse:.4f}")