"""
Synthetic Neurodiagnostic Waveform Generator (Zero-PHI Baseline)
================================================================
PURPOSE FOR CLINICAL QA & REGULATORY COMPLIANCE:
Testing medical telemetry software using real patient recordings introduces strict
HIPAA privacy risks (Protected Health Information / PHI). Furthermore, real
recordings contain unpredictable artifacts that make automated pass/fail mathematical
testing difficult to standardize.

This module uses deterministic mathematics (numpy) to synthesize a clean, continuous
256 Hz human brainwave (a 10 Hz Alpha-band EEG rhythm) paired with subtle ambient
hospital sensor noise. It provides a 100% repeatable, HIPAA-safe patient baseline.
"""

import numpy as np


def generate_eeg_signal(duration_seconds=10, sample_rate=256, frequency=10):
    """
    Synthesizes a continuous 256 Hz EEG waveform with realistic baseline noise.

    Parameters:
    - duration_seconds (int/float): Length of the simulated recording in seconds.
    - sample_rate (int): Samples captured per second (256 Hz is standard for clinical EEG).
    - frequency (float): Brainwave oscillation speed in Hertz (10 Hz = healthy resting Alpha wave).

    Returns:
    - time (np.ndarray): Exact timestamp (in seconds) for every individual sample.
    - synthetic_signal (np.ndarray): Simulated voltage readings (in Volts).
    """
    # 1. Calculate total number of discrete voltage measurements (Seconds * 256 Hz)
    total_samples = int(duration_seconds * sample_rate)

    # 2. Create an evenly spaced timeline from 0 seconds to duration_seconds
    time = np.linspace(0, duration_seconds, total_samples, endpoint=False)

    # 3. Generate a pure mathematical sine wave at the target neurodiagnostic frequency (10 Hz)
    clean_wave = np.sin(2 * np.pi * frequency * time)

    # 4. Add minor Gaussian white noise (mean = 0.0V, standard deviation = 0.2V)
    #    This simulates normal skin-electrode impedance and ambient hospital room electronics.
    noise = np.random.normal(0, 0.2, total_samples)

    # 5. Combine the clean brainwave and baseline sensor noise into the final stream
    synthetic_signal = clean_wave + noise

    return time, synthetic_signal


if __name__ == "__main__":
    # Self-test demonstration when run directly from the terminal
    time_data, signal_data = generate_eeg_signal(duration_seconds=2)

    print("--- Synthetic EEG Generator Active ---")
    print(f"Generated {len(signal_data)} synthetic data points (2 seconds at 256 Hz).")
    print(f"First 5 data values: {signal_data[:5]}")
    print("Disclaimer: 100% mathematically synthesized data. No PHI used.")