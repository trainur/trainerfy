import os
import gc
import librosa
import numpy as np
import hashlib
import matplotlib.pyplot as plt
from scipy.ndimage import maximum_filter
from collections import defaultdict

SR = 22050
HOP_LENGTH = 512
FAN_OUT = 10
N_PEAKS_PER_FRAME = 10
TIME_WINDOW = 2.5
DB_THRESHOLD = -30
FILTER_SIZE = (20, 20)

SPECTROGRAM_PATH = "spectrograms"

def save_spectrogram_image(spectrogram, filename):
    os.makedirs(SPECTROGRAM_PATH, exist_ok=True)

    title = f"{filename} Spectrogram"

    fig, ax = plt.subplots(figsize=(10, 4))
    
    img = librosa.display.specshow(
        spectrogram,
        sr=SR,
        hop_length=HOP_LENGTH,
        x_axis='time',
        y_axis='log',
        ax=ax
    )
    
    fig.colorbar(img, ax=ax, format='%+2.0f dB')
    ax.set_title(title)
    fig.tight_layout()
    
    path = os.path.join(SPECTROGRAM_PATH, f"{filename}.png")
    fig.savefig(path, dpi=100)
    plt.close(fig)
    plt.clf()
    plt.cla()
    gc.collect()
    
    print(f"Saved spectrogram image to {path}")

def get_spectrogram(audio):
    # Compute the spectrogram using Short-Time Fourier Transform (STFT)
    stft = np.abs(librosa.stft(audio, hop_length=HOP_LENGTH))
    return librosa.amplitude_to_db(stft)

def get_peaks(spectrogram, threshold=DB_THRESHOLD, max_peaks_per_frame=N_PEAKS_PER_FRAME):
    neighbourhood = maximum_filter(spectrogram, size=FILTER_SIZE)

    peaks = (spectrogram == neighbourhood)
    peaks = peaks & (spectrogram > threshold)

    peak_coords = np.argwhere(peaks)  # (freq, time)

    # Store peak strengths
    peaks_with_strength = [
        (int(freq), int(time), float(spectrogram[freq, time]))

        for freq, time in peak_coords
    ]

    # Group by time frame
    by_time = defaultdict(list)
    for freq, time, strength in peaks_with_strength:
        by_time[time].append((freq, strength))

    # How many freq bins correspond to kick drum (~20-100hz)
    # bins_per_hz = n_fft / SR, n_fft defaults to 2048
    kick_cutoff = int(100 * 2048 / SR)  # ~4 bins
    print(f"Kick cutoff bin: {kick_cutoff}")

    limited_peaks = []

    for time, values in by_time.items():
        # Keep strongest peaks in this time frame
        values.sort(key=lambda x: x[1], reverse=True)

        for freq, strength in values[:max_peaks_per_frame]:
            if freq >= kick_cutoff:  # Skip kick drum frequencies
                limited_peaks.append((freq, time))

    # Sort by time, then frequency
    limited_peaks.sort(key=lambda x: (x[1], x[0]))

    return limited_peaks

def hash_peaks(peaks):
    hashes = []
    peaks = sorted(peaks, key=lambda p: p[1])
    for i, (freq1, time1) in enumerate(peaks):
        for freq2, time2 in peaks[i+1:i+FAN_OUT+1]:
            delta_time = time2 - time1
            if 0 < delta_time < TIME_WINDOW * (SR / HOP_LENGTH):
                h = int(hashlib.md5(f"{freq1}|{freq2}|{delta_time}".encode()).hexdigest()[:8], 16)
                hashes.append((h, time1))
    return hashes

def generate_song_fingerprint(audio_path, save_spectrogram=False):
    audio, sr = librosa.load(audio_path, sr=SR)
    print(f"Duration: {len(audio)/sr:.2f}s")
    print(f"Max amplitude: {audio.max():.4f}")
    print(f"Mean amplitude: {audio.mean():.4f}")

    spectrogram = get_spectrogram(audio)
    print(f"Spectrogram shape: {spectrogram.shape}")

    if save_spectrogram:
        filename = os.path.basename(audio_path)
        filename = filename.replace(".mp3", "")
        filename = filename.replace(" ", "_")
        save_spectrogram_image(spectrogram, filename)
        print(f"Saved spectrogram image to {audio_path}.spectrogram.png")

    peaks = get_peaks(spectrogram)
    print(f"Total peaks: {len(peaks)}")

    hashes = hash_peaks(peaks)
    print(f"Total hashes: {len(hashes)}\n----------------------------------")
    return hashes