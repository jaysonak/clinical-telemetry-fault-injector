import numpy as np
import pytest
from src.generator import generate_eeg_signal
from src.injector import inject_packet_loss, inject_latency_jitter
from src.dsp_processor import interpolate_missing_packets, smooth_signal


def test_total_blackout_raises_clinical_alert():
    """
    Release Gate 3: If hospital Wi-Fi suffers 100% packet loss, the DSP processor
    must explicitly raise a ValueError rather than silently graphing flatline zeros.
    """
    _, clean_signal = generate_eeg_signal(duration_seconds=2)
    blackout_signal = inject_packet_loss(clean_signal, drop_rate=1.0, packet_size=16)

    with pytest.raises(ValueError, match="100% packet drop"):
        interpolate_missing_packets(blackout_signal)


def test_invalid_smoothing_window_rejected():
    """
    Release Gate 4: Ensures invalid filter parameters are caught immediately.
    """
    _, clean_signal = generate_eeg_signal(duration_seconds=1)

    with pytest.raises(ValueError, match="Window size must be at least 1"):
        smooth_signal(clean_signal, window_size=0)


def test_latency_jitter_bounds():
    """
    Release Gate 5: Confirms network transport jitter simulation stays strictly
    within the specified millisecond boundary.
    """
    np.random.seed(42)
    time_array, _ = generate_eeg_signal(duration_seconds=2)
    max_jitter_ms = 5.0

    jittered_time = inject_latency_jitter(time_array, max_jitter_ms=max_jitter_ms)
    max_observed_delta_ms = np.max(np.abs(jittered_time - time_array)) * 1000.0

    assert max_observed_delta_ms <= max_jitter_ms + 1e-6