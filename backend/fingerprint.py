"""
fingerprint.py
--------------
Ye file audio ko "fingerprint" mein badalti hai - bilkul wahi
process jo humne discuss kiya tha:

  Audio -> Spectrogram -> Peaks (star map) -> Hashes

Is file mein 3 main functions hain, jo teeno steps ko represent
karte hain.
"""

import numpy as np
import librosa
from scipy.ndimage import maximum_filter
import hashlib


# ---------- STEP 1: Spectrogram Banana ----------
def create_spectrogram(audio_path):
    """
    Audio file leti hai, aur uska spectrogram (frequency vs time
    vs loudness) nikaal kar deti hai.
    """

    # librosa.load() audio file ko numpy array mein load karta hai.
    # 'y' = audio ki actual waveform (numbers ki list)
    # 'sr' = sample rate (1 second mein kitne samples liye gaye, jaise 22050)
    y, sr = librosa.load(audio_path, sr=22050, mono=True)

    # STFT (Short-Time Fourier Transform) audio ko chote-chote
    # time-windows mein todta hai aur har window ka FFT nikaalta hai.
    # n_fft = ek window mein kitne samples honge
    # hop_length = agla window kitna aage se shuru hoga (overlap ke liye)
    n_fft = 2048
    hop_length = 512
    stft_result = librosa.stft(y, n_fft=n_fft, hop_length=hop_length)

    # stft_result complex numbers deta hai, hume sirf loudness
    # (magnitude) chahiye - isliye absolute value lete hain.
    spectrogram = np.abs(stft_result)

    # Decibel scale mein convert karna - insaan loudness ko
    # is scale mein zyada behtar samajhte hain (log scale hai).
    spectrogram_db = librosa.amplitude_to_db(spectrogram, ref=np.max)

    return spectrogram_db, sr, hop_length


# ---------- STEP 2: Fingerprinting (Star Map / Peaks nikalna) ----------
def extract_peaks(spectrogram_db, amplitude_threshold=-40, neighborhood_size=20):
    """
    Poore spectrogram mein se sirf wo points nikaalti hai jo apne
    aas-paas ke area mein sabse zyada loud (dominant) hain.
    Yehi humara "star map" bante hain.
    """

    # maximum_filter har point ko check karta hai: "kya ye apne
    # aas-paas (neighborhood_size wale area) mein sabse zyada loud hai?"
    local_max = maximum_filter(spectrogram_db, size=neighborhood_size) == spectrogram_db

    # Bohot dheeme (halke) points ko hata dena - warna silence
    # ya background noise bhi "peak" ban jayega.
    loud_enough = spectrogram_db > amplitude_threshold

    # Dono conditions sach honi chahiye: local peak HO aur loud bhi ho
    peak_mask = local_max & loud_enough

    # peak_mask mein True/False hai; hum un sab positions ko nikaalte
    # hain jahan True hai (yani wahan ek "star" hai)
    freq_indices, time_indices = np.where(peak_mask)

    # Peaks ko ek list of (time, frequency) tuples ke form mein return karna
    peaks = list(zip(time_indices.tolist(), freq_indices.tolist()))

    return peaks


# ---------- STEP 3: Hash Generation ----------
def generate_hashes(peaks, fan_out=5, min_time_delta=1, max_time_delta=200):
    """
    Peaks ke pairs banati hai (anchor + target) aur har pair se
    ek unique hash banati hai. Ye hash hi database mein store hoga.
    """

    # Peaks ko time ke hisaab se sort karna zaroori hai, taake
    # hum har anchor ke "aage" wale points ko target bana sakein.
    peaks_sorted = sorted(peaks, key=lambda p: p[0])

    hashes = []

    for i in range(len(peaks_sorted)):
        anchor_time, anchor_freq = peaks_sorted[i]

        # Fan-out: har anchor point ko sirf agle 'fan_out' number
        # ke peaks ke sath pair karna (sab ke sath nahi - warna
        # bohot zyada hashes ban jayenge)
        for j in range(1, fan_out + 1):
            if i + j >= len(peaks_sorted):
                break

            target_time, target_freq = peaks_sorted[i + j]
            time_delta = target_time - anchor_time

            # Sirf reasonable time-gap wale pairs lena
            # (bohot paas ya bohot door wale pairs useful nahi hote)
            if min_time_delta <= time_delta <= max_time_delta:

                # Ye teen values mila kar ek unique hash banti hai:
                # anchor ki frequency, target ki frequency, aur
                # dono ke beech time ka farak
                raw_string = f"{anchor_freq}|{target_freq}|{time_delta}"

                # hashlib se ek fixed-length, unique hash string banana
                hash_value = hashlib.sha1(raw_string.encode()).hexdigest()[:20]

                hashes.append((hash_value, anchor_time))

    return hashes


# ---------- Sab kuch jodne wala main function ----------
def fingerprint_audio(audio_path):
    """
    Ye function upar wale teeno steps ko ek sath chalata hai.
    Backend ke doosre parts (add-song, identify) isi function ko call karenge.
    """
    spectrogram_db, sr, hop_length = create_spectrogram(audio_path)
    peaks = extract_peaks(spectrogram_db)
    hashes = generate_hashes(peaks)

    print(f"Total peaks (stars) mile: {len(peaks)}")
    print(f"Total hashes (fingerprints) bane: {len(hashes)}")

    return hashes


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        fingerprint_audio(sys.argv[1])
    else:
        print("Usage: python fingerprint.py <audio_file_path>")