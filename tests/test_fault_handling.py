"""
Automated Clinical Fail-Safe & Boundary Release Gates
=====================================================
PURPOSE FOR PATIENT SAFETY:
Medical software must not only recover from minor wireless glitches—it must also
know when a situation is too dangerous to guess. For example, if a patient's wireless
transmitter completely dies (100% packet loss), the software must NEVER draw a fake
smooth line on the monitor. It must immediately trigger a loud clinical alert.

These automated pytest assertions verify fail-safe alarms and strict parameter bounds.
"""

import numpy as np
import pytest
from src.generator import generate_eeg_signal
from src.injector import inject_packet_loss, inject_latency_jitter
from src.dsp_processor import interpolate_missing_packets, smooth_signal


def test_total_blackout_raises_clinical_alert():
    """
    Release Gate 3 (Total Blackout Fail-Safe):
    Simulates a complete 100% hospital Wi-Fi disconnect or dead sensor battery.
    Verifies that the DSP processor explicitly raises a ValueError alarm rather
    than silently drawing a deceptive flatline on the clinical display.
    """
    _, clean_signal = generate_eeg_signal(duration_seconds=2)

    # Force 100% of packets to drop (drop_rate=1.0)
    blackout_signal = inject_packet_loss(clean_signal, drop_rate=1.0, packet_size=16)

    # The test only passes if the software actively raises the "100% packet drop" alarm
    with pytest.raises(ValueError, match="100% packet drop"):
        interpolate_missing_packets(blackout_signal)


def test_invalid_smoothing_window_rejected():
    """
    Release Gate 4 (Defensive Configuration Check):
    Verifies that accidental misconfiguration of the DSP smoothing filter (such as a
    zero or negative window size) is caught immediately before corrupting patient data.
    """
    _, clean_signal = generate_eeg_signal(duration_seconds=1)

    with pytest.raises(ValueError, match="Window size must be at least 1"):
        smooth_signal(clean_signal, window_size=0)


def test_latency_jitter_bounds():
    """
    Release Gate 5 (Asynchronous Transport Timing Verification):
    Confirms that simulated hospital network transport jitter stays strictly
    bounded within the expected millisecond envelope.
    """
    np.random.seed(42)
    time_array, _ = generate_eeg_signal(duration_seconds=2)
    max_jitter_ms = 5.0

    jittered_time = inject_latency_jitter(time_array, max_jitter_ms=max_jitter_ms)
    max_observed_delta_ms = np.max(np.abs(jittered_time - time_array)) * 1000.0

    # Verify timestamp drift never exceeds the 5.0 ms tolerance ceiling
    assert max_observed_delta_ms <= max_jitter_ms + 1e-6