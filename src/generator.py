import numpy as np

def generate_eeg_signal(duration_seconds=10, sample_rate=256, frequency=10):
    """
    Generates a synthetic EEG sine wave with randomized baseline noise.
    """
    # 1. Create a timeline (total data points = seconds * Hz)
    total_samples = duration_seconds * sample_rate
    
    # np.linspace creates an evenly spaced array of time values
    time = np.linspace(0, duration_seconds, total_samples, endpoint=False)
    
    # 2. Generate the perfect clean sine wave (simulating a healthy 10Hz Alpha brainwave)
    clean_wave = np.sin(2 * np.pi * frequency * time)
    
    # 3. Add minor randomized noise to simulate real-world hospital interference
    noise = np.random.normal(0, 0.2, total_samples)
    
    # 4. Combine them for the final synthetic diagnostic signal
    synthetic_signal = clean_wave + noise
    
    return time, synthetic_signal

if __name__ == "__main__":
    # Test the generator by creating 2 seconds of data
    time_data, signal_data = generate_eeg_signal(duration_seconds=2)
    
    print("--- Synthetic EEG Generator Active ---")
    print(f"Generated {len(signal_data)} synthetic data points (2 seconds at 256 Hz).")
    print(f"First 5 data values: {signal_data[:5]}")
    print("Disclaimer: 100% mathematically synthesized data. No PHI used.")