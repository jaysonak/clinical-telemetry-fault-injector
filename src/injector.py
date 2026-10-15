"""
Multi-Node Hospital Network & Hardware Fault Injector
=====================================================
PURPOSE FOR CLINICAL QA:
Wireless bedside monitors and ambulatory EEG/EMG packs transmit patient data
across busy hospital Wi-Fi networks. Manual QA testing typically tests software
on a stable desk connection, completely missing real-world wireless failures.

This module intentionally corrupts clean telemetry streams with three real-world
hospital hazards:
1. Wi-Fi Dead Zones & Roaming Drops (Contiguous NaN packet loss)
2. Physical Electrode Bump / Defibrillator / Machinery Interference (+/- 50V spikes)
3. Congested Hospital Router Queues (Millisecond packet arrival jitter)
"""

import numpy as np

# Compatible whether run directly or via pytest from the root folder
try:
    from src.generator import generate_eeg_signal
except ImportError:
    from generator import generate_eeg_signal


def inject_packet_loss(signal, drop_rate=0.05, packet_size=16):
    """
    FAULT CONDITION 1: Wireless Packet Loss (NaN Dropouts)
    Why this matters: Wireless transmitters send EEG data in small bundles (packets)
    of 16 samples. When a patient walks past an elevator shaft or switches Wi-Fi
    access points, entire packets vanish. Missing packets arrive at the clinical
    receiver as 'NaN' (Not a Number), which can crash unprepared graphing software.
    """
    corrupted = signal.copy().astype(float)
    num_packets = len(corrupted) // packet_size

    # Iterate through each wireless transmission packet and randomly drop based on drop_rate
    for i in range(num_packets):
        if np.random.rand() < drop_rate:
            start = i * packet_size
            end = start + packet_size
            corrupted[start:end] = np.nan

    return corrupted


def inject_anomalous_spikes(signal, spike_probability=0.01, spike_magnitude=50.0):
    """
    FAULT CONDITION 2: High-Voltage Hardware & Electromagnetic Transients
    Why this matters: If a patient tugs on a lead wire or nearby surgical/imaging
    equipment discharges, a sudden 50-volt spike can enter the amplifier. Since a real
    brainwave is tiny, an unfiltered 50V spike ruins automated seizure detection and
    blows out the visual scale on the nurse's monitor.
    """
    corrupted = signal.copy().astype(float)

    # Select random moments in time where hardware interference strikes
    spike_mask = np.random.rand(len(corrupted)) < spike_probability

    # Randomly assign positive (+50V) or negative (-50V) polarity to each spike
    signs = np.random.choice([-1, 1], size=len(corrupted))
    corrupted[spike_mask] += signs[spike_mask] * spike_magnitude

    return corrupted


def inject_latency_jitter(time_array, max_jitter_ms=5.0):
    """
    FAULT CONDITION 3: Asynchronous Network Transport Jitter
    Why this matters: When hospital network switches are congested with electronic
    health record (EHR) traffic, telemetry packets arrive slightly early or late.
    This function perturbs packet timestamps within a +/- millisecond window to
    verify time-domain stability.
    """
    # Convert milliseconds to seconds and apply random uniform delay/advance
    jitter_seconds = np.random.uniform(
        -max_jitter_ms / 1000.0,
        max_jitter_ms / 1000.0,
        size=len(time_array),
    )
    return time_array + jitter_seconds


if __name__ == "__main__":
    # Self-test demonstration when run directly from the terminal
    time_data, clean_signal = generate_eeg_signal(duration_seconds=2)

    lossy_signal = inject_packet_loss(clean_signal, drop_rate=0.15, packet_size=16)
    spiked_signal = inject_anomalous_spikes(lossy_signal, spike_probability=0.02)
    jittered_time = inject_latency_jitter(time_data, max_jitter_ms=8.0)

    missing_samples = np.isnan(spiked_signal).sum()
    extreme_spikes = np.sum(np.abs(np.nan_to_num(spiked_signal)) > 10.0)

    print("--- Multi-Node Fault Injector Active ---")
    print(f"Baseline Samples: {len(clean_signal)}")
    print(f"Samples Dropped (NaN Packet Loss): {missing_samples}")
    print(f"Anomalous Hardware Spikes Injected: {extreme_spikes}")
    print(f"Max Timestamp Jitter (ms): {np.max(np.abs(jittered_time - time_data)) * 1000:.2f} ms")