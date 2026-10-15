import os
import numpy as np
import matplotlib.pyplot as plt

try:
    from src.generator import generate_eeg_signal
    from src.injector import inject_packet_loss, inject_anomalous_spikes
    from src.dsp_processor import process_telemetry_stream
except ImportError:
    from generator import generate_eeg_signal
    from injector import inject_packet_loss, inject_anomalous_spikes
    from dsp_processor import process_telemetry_stream


def generate_clinical_recovery_chart(output_path="assets/eeg_recovery_demo.png"):
    """
    Generates a 3-panel visual comparison of the synthetic EEG signal,
    the corrupted hospital Wi-Fi telemetry stream, and the DSP-recovered output.
    """
    np.random.seed(42)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # 1. Generate 2 seconds of 256 Hz EEG data
    time_data, clean_signal = generate_eeg_signal(duration_seconds=2, sample_rate=256)

    # 2. Inject packet loss (NaN gaps) and hardware voltage spikes
    corrupted_signal = inject_packet_loss(clean_signal, drop_rate=0.15, packet_size=16)
    corrupted_signal = inject_anomalous_spikes(
        corrupted_signal, spike_probability=0.015, spike_magnitude=25.0
    )

    # 3. Recover the signal through the clinical DSP pipeline
    recovered_signal = process_telemetry_stream(
        corrupted_signal, max_voltage=5.0, smoothing_window=5
    )
    rmse = np.sqrt(np.mean((clean_signal - recovered_signal) ** 2))

    # 4. Plot the 3-panel figure
    fig, axes = plt.subplots(3, 1, figsize=(11, 7), sharex=True)
    fig.suptitle(
        "Clinical Telemetry Fault Injection & Automated DSP Parity Verification (256 Hz)",
        fontsize=13,
        fontweight="bold",
    )

    # Panel 1: Clean Baseline
    axes[0].plot(time_data, clean_signal, color="#1f77b4", linewidth=1.2)
    axes[0].set_title(
        "1. Baseline Synthetic Patient EEG (10 Hz Alpha Wave + Baseline Noise)",
        fontsize=10,
        fontweight="bold",
    )
    axes[0].set_ylabel("Amplitude (V)")
    axes[0].set_ylim(-2.5, 2.5)
    axes[0].grid(True, linestyle="--", alpha=0.5)

    # Panel 2: Corrupted Stream (Highlight dropped packets in red shading)
    axes[1].plot(time_data, corrupted_signal, color="#d62728", linewidth=1.2)
    nan_mask = np.isnan(corrupted_signal)
    axes[1].fill_between(
        time_data, -30, 30, where=nan_mask, color="#ff9896", alpha=0.4, label="Dropped Wi-Fi Packets (NaN)"
    )
    axes[1].set_title(
        "2. Degraded Hospital Telemetry Stream (Wi-Fi Packet Loss + Hardware Voltage Spikes)",
        fontsize=10,
        fontweight="bold",
    )
    axes[1].set_ylabel("Amplitude (V)")
    axes[1].set_ylim(-28, 28)
    axes[1].legend(loc="upper right", fontsize=8)
    axes[1].grid(True, linestyle="--", alpha=0.5)

    # Panel 3: Recovered Signal vs Baseline
    axes[2].plot(
        time_data, clean_signal, color="#aec7e8", linewidth=1.0, linestyle="--", label="Original Baseline"
    )
    axes[2].plot(
        time_data, recovered_signal, color="#2ca02c", linewidth=1.4, label=f"DSP Reconstructed (RMSE: {rmse:.3f})"
    )
    axes[2].set_title(
        "3. DSP-Reconstructed Telemetry Output (100% Dropouts Interpolated & Spikes Clamped)",
        fontsize=10,
        fontweight="bold",
    )
    axes[2].set_xlabel("Time (Seconds)")
    axes[2].set_ylabel("Amplitude (V)")
    axes[2].set_ylim(-2.5, 2.5)
    axes[2].legend(loc="upper right", fontsize=8)
    axes[2].grid(True, linestyle="--", alpha=0.5)

    plt.tight_layout()
    plt.savefig(output_path, dpi=200)
    plt.close()
    print(f"--- Visual Telemetry Chart Saved to: {output_path} ---")


if __name__ == "__main__":
    generate_clinical_recovery_chart()