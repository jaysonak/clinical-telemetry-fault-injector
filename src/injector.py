import numpy as np

# Compatible whether run directly or via pytest from the root folder
try:
    from src.generator import generate_eeg_signal
except ImportError:
    from generator import generate_eeg_signal


def inject_packet_loss(signal, drop_rate=0.05, packet_size=16):
    """
    Simulates dropped Wi-Fi packets in a hospital telemetry network
    by replacing contiguous chunks of signal data with NaN (Not a Number).
    """
    corrupted = signal.copy().astype(float)
    num_packets = len(corrupted) // packet_size

    for i in range(num_packets):
        if np.random.rand() < drop_rate:
            start = i * packet_size
            end = start + packet_size
            corrupted[start:end] = np.nan

    return corrupted


def inject_anomalous_spikes(signal, spike_probability=0.01, spike_magnitude=50.0):
    """
    Simulates sudden hardware interference or electrode movement
    by injecting extreme mathematical voltage spikes.
    """
    corrupted = signal.copy().astype(float)
    spike_mask = np.random.rand(len(corrupted)) < spike_probability
    # Randomly assign positive or negative polarity to the spikes
    signs = np.random.choice([-1, 1], size=len(corrupted))
    corrupted[spike_mask] += signs[spike_mask] * spike_magnitude

    return corrupted


def inject_latency_jitter(time_array, max_jitter_ms=5.0):
    """
    Simulates asynchronous network transport jitter by perturbing
    packet arrival timestamps (in seconds).
    """
    jitter_seconds = np.random.uniform(
        -max_jitter_ms / 1000.0,
        max_jitter_ms / 1000.0,
        size=len(time_array)
    )
    return time_array + jitter_seconds


if __name__ == "__main__":
    # 1. Generate a clean 2-second baseline signal (512 samples)
    time_data, clean_signal = generate_eeg_signal(duration_seconds=2)

    # 2. Apply multi-node fault conditions
    lossy_signal = inject_packet_loss(clean_signal, drop_rate=0.15, packet_size=16)
    spiked_signal = inject_anomalous_spikes(lossy_signal, spike_probability=0.02)
    jittered_time = inject_latency_jitter(time_data, max_jitter_ms=8.0)

    # 3. Calculate diagnostic telemetry metrics
    missing_samples = np.isnan(spiked_signal).sum()
    extreme_spikes = np.sum(np.abs( np.nan_to_num(spiked_signal) ) > 10.0)

    print("--- Multi-Node Fault Injector Active ---")
    print(f"Baseline Samples: {len(clean_signal)}")
    print(f"Samples Dropped (NaN Packet Loss): {missing_samples}")
    print(f"Anomalous Hardware Spikes Injected: {extreme_spikes}")
    print(f"Max Timestamp Jitter (ms): {np.max(np.abs(jittered_time - time_data)) * 1000:.2f} ms")