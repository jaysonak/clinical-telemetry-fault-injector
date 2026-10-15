"""
Clinical Digital Signal Processing (DSP) & Fault Recovery Module
================================================================
PURPOSE FOR CLINICAL QA:
When wireless patient monitors (EEG/EMG) transmit over hospital Wi-Fi, network
dropouts and electrical interference corrupt the data stream. If unhandled, this
corruption can crash clinical graphing software or trigger false alarms.

This module acts as the fault-tolerant clinical receiver. It repairs missing data
packets, clamps dangerous voltage spikes, smooths high-frequency sensor noise,
and verifies that the patient's underlying brainwave frequency (10 Hz) was not
distorted during recovery.
"""

import numpy as np

try:
    from src.generator import generate_eeg_signal
    from src.injector import inject_packet_loss, inject_anomalous_spikes
except ImportError:
    from generator import generate_eeg_signal
    from injector import inject_packet_loss, inject_anomalous_spikes


def interpolate_missing_packets(signal):
    """
    CLINICAL SAFETY GATE 1: Packet Loss Recovery
    Why this matters: Dropped Wi-Fi packets arrive as 'NaN' (Not a Number).
    Standard math libraries crash or render blank screens when encountering NaNs.
    This function bridges short wireless dropouts using linear interpolation,
    and explicitly raises a clinical alert if the connection is 100% lost.
    """
    reconstructed = signal.copy().astype(float)
    nan_mask = np.isnan(reconstructed)

    # If zero packets were dropped, return the clean signal immediately
    if not np.any(nan_mask):
        return reconstructed

    # PATIENT SAFETY CHECK: If 100% of packets are missing, the sensor is disconnected.
    # Never guess or draw a fake flatline during a total blackout—raise an explicit alarm.
    if np.all(nan_mask):
        raise ValueError("Telemetry stream completely lost: 100% packet drop.")

    # Locate valid data points and mathematically bridge the missing gaps between them
    valid_indices = np.where(~nan_mask)[0]
    missing_indices = np.where(nan_mask)[0]

    reconstructed[nan_mask] = np.interp(
        missing_indices, valid_indices, reconstructed[valid_indices]
    )
    return reconstructed


def suppress_hardware_spikes(signal, max_physiological_voltage=5.0):
    """
    CLINICAL SAFETY GATE 2: Transient Artifact Suppression
    Why this matters: Physical movement of an electrode or nearby hospital machinery
    can inject massive voltage spikes (e.g., 50V) that are biologically impossible
    for a human brain to produce. Left unfiltered, these spikes ruin automated
    diagnostic scoring. This function detects voltages exceeding human physiological
    limits and replaces them with clean interpolated values.
    """
    filtered = signal.copy().astype(float)

    # Identify any sample exceeding normal human physiological range (default: +/- 5.0V)
    spike_mask = np.abs(filtered) > max_physiological_voltage

    # Mark extreme hardware spikes as missing (NaN) and smoothly interpolate across them
    filtered[spike_mask] = np.nan
    return interpolate_missing_packets(filtered)


def smooth_signal(signal, window_size=5):
    """
    CLINICAL SAFETY GATE 3: High-Frequency Baseline Noise Attenuation
    Why this matters: Hospital rooms have ambient electrical noise. A moving-average
    convolution filter smooths out microscopic jitter while keeping the broader
    diagnostic brainwave intact.
    """
    if window_size < 1:
        raise ValueError("Window size must be at least 1.")

    kernel = np.ones(window_size) / window_size
    return np.convolve(signal, kernel, mode="same")


def compute_dominant_frequency(signal, sample_rate=256):
    """
    CLINICAL SAFETY GATE 4: Spectral Frequency Parity (Fast Fourier Transform / FFT)
    Why this matters: In neurodiagnostics (EEG), doctors diagnose conditions based on
    wave frequency (e.g., a 10 Hz Alpha wave indicates a healthy resting brain, while
    a 3 Hz wave may indicate seizure activity). We must mathematically prove that
    repairing dropped Wi-Fi packets did NOT warp the frequency of the patient's wave.
    """
    # Remove any baseline DC offset before running the Fast Fourier Transform
    centered_signal = signal - np.mean(signal)

    # Convert the signal from the Time Domain into the Frequency Domain (Hz)
    fft_magnitudes = np.abs(np.fft.rfft(centered_signal))
    fft_frequencies = np.fft.rfftfreq(len(centered_signal), d=1.0 / sample_rate)

    # Identify the strongest frequency (in Hz) present in the signal
    dominant_index = np.argmax(fft_magnitudes)
    return float(fft_frequencies[dominant_index])


def process_telemetry_stream(raw_corrupted_signal, max_voltage=5.0, smoothing_window=5):
    """
    Executes the end-to-end clinical telemetry recovery pipeline in sequence:
    1. Reconstruct missing Wi-Fi packets (NaNs)
    2. Clamp non-physiological hardware voltage spikes
    3. Smooth ambient baseline noise
    """
    step1_packet_recovered = interpolate_missing_packets(raw_corrupted_signal)
    step2_spike_suppressed = suppress_hardware_spikes(
        step1_packet_recovered, max_physiological_voltage=max_voltage
    )
    step3_smoothed = smooth_signal(step2_spike_suppressed, window_size=smoothing_window)
    return step3_smoothed


if __name__ == "__main__":
    # Self-test demonstration when run directly from the terminal
    np.random.seed(42)
    _, clean_signal = generate_eeg_signal(duration_seconds=4, sample_rate=256, frequency=10)

    corrupted = inject_packet_loss(clean_signal, drop_rate=0.15, packet_size=16)
    corrupted = inject_anomalous_spikes(corrupted, spike_probability=0.02)

    recovered_signal = process_telemetry_stream(corrupted)

    remaining_nans = np.isnan(recovered_signal).sum()
    rmse = np.sqrt(np.mean((clean_signal - recovered_signal) ** 2))
    recovered_freq = compute_dominant_frequency(recovered_signal, sample_rate=256)

    print("--- Clinical DSP Processor & Spectral Analyzer Active ---")
    print(f"Remaining NaN Dropouts After DSP: {remaining_nans}")
    print(f"Max Voltage After Spike Suppression: {np.max(np.abs(recovered_signal)):.2f} V")
    print(f"Signal Recovery Root Mean Square Error (RMSE): {rmse:.4f}")
    print(f"Recovered Dominant Brainwave Frequency (FFT): {recovered_freq:.2f} Hz (Target: 10.00 Hz)")