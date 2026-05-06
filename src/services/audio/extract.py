import librosa
import pyprojroot as ppr
from PIL import Image
import io
from librosa.util.exceptions import LibrosaError
import logging
import os
import torch
import torch.nn.functional as F
import torchcrepe
from pydub import AudioSegment
import numpy as np
import math

logger = logging.getLogger(__name__)
logging.basicConfig(level='DEBUG')

TARGET_SR = 16000
MIN_DUR = 0.15
MAX_DUR = 5.0
RMS_THRESHOLD = 0.01

label_map = {
    -1: "unknown",
    0: "normal",
    1: "down",
    2: "up"
}


def load_audio(audio: bytes | str):
    # m4a и другие форматы не поддерживаемые soundfile — грузим через pydub
    if isinstance(audio, str) and audio.lower().endswith(".m4a"):
        return _load_via_pydub(audio)

    if isinstance(audio, bytes):
        # Пытаемся определить формат по заголовку
        if _is_m4a_bytes(audio):
            return _load_via_pydub(audio)
        return librosa.load(io.BytesIO(audio), sr=TARGET_SR)

    return librosa.load(audio, sr=TARGET_SR)


def _load_via_pydub(audio: bytes | str) -> tuple:
    if isinstance(audio, bytes):
        segment = AudioSegment.from_file(io.BytesIO(audio), format="m4a")
    else:
        segment = AudioSegment.from_file(audio, format="m4a")

    # Конвертируем в mono float32 numpy array
    samples = np.array(segment.get_array_of_samples(), dtype=np.float32)

    if segment.channels == 2:
        samples = samples.reshape(-1, 2).mean(axis=1)

    # Нормализуем в диапазон [-1, 1]
    samples /= np.iinfo(segment.array_type).max

    # Ресемплируем если нужно
    if segment.frame_rate != TARGET_SR:
        samples = librosa.resample(samples, orig_sr=segment.frame_rate, target_sr=TARGET_SR)

    return samples, TARGET_SR


def _is_m4a_bytes(data: bytes) -> bool:
    # M4A/MP4 содержит 'ftyp' box на байтах 4–8
    return len(data) > 8 and data[4:8] == b"ftyp"


def segment_audio(y, sr):
    """
    Нарезает аудио на сегменты по границам нот.
    Логика идентична process_single_file из пайплайна обучения.
    """
    segments = []

    # Убираем тишину в начале и конце
    y, _ = librosa.effects.trim(y, top_db=25)

    onset_frames = librosa.onset.onset_detect(
        y=y, sr=sr,
        backtrack=True,
        delta=0.07,
        wait=6
    )

    if len(onset_frames) == 0:
        return segments

    onset_samples = librosa.frames_to_samples(onset_frames)
    boundaries = np.concatenate([onset_samples, [len(y)]])

    for i in range(len(boundaries) - 1):
        start = int(boundaries[i])
        end = int(boundaries[i + 1])
        segment = y[start:end]

        # Обрезаем decay-хвост
        segment_trimmed, trim_idx = librosa.effects.trim(segment, top_db=25)

        duration = len(segment_trimmed) / sr
        if duration < MIN_DUR or duration > MAX_DUR:
            continue

        rms = np.sqrt(np.mean(segment_trimmed ** 2))
        if rms < RMS_THRESHOLD:
            continue

        real_start = start + trim_idx[0]

        segments.append({
            'y': segment_trimmed,
            'sr': sr,
            'start': real_start / sr,
            'duration': duration
        })

    return segments


def get_cqt(y, sr, n_bins=168, bins_per_octave=24, processor=None):
    """CQT с фолбэком на мел для коротких сегментов."""
    try:
        cqt = librosa.cqt(
            y, sr=sr,
            n_bins=n_bins,
            bins_per_octave=bins_per_octave,
            fmin=librosa.note_to_hz('B0')
        )
        cqt_db = librosa.amplitude_to_db(np.abs(cqt), ref=np.max)

        spec_min, spec_max = cqt_db.min(), cqt_db.max()
        spec_scaled = 255 * (cqt_db - spec_min) / (spec_max - spec_min + 1e-6)
        spec_uint8 = spec_scaled.astype(np.uint8)

        image = Image.fromarray(spec_uint8).convert("RGB")
        if processor:
            image = processor(images=image, return_tensors='pt')
        return image
    except Exception as e:
        logger.error(f"Ошибка при получении CQT: {e}")
        raise


def get_mel_spec(y, sr, processor=None, n_mels: int = 128):
    try:
        mel_spec = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=n_mels)
        mel_spec_db = librosa.power_to_db(mel_spec, ref=np.max)

        spec_min, spec_max = mel_spec_db.min(), mel_spec_db.max()
        spec_scaled = 255 * (mel_spec_db - spec_min) / (spec_max - spec_min + 1e-6)
        spec_uint8 = spec_scaled.astype(np.uint8)

        image = Image.fromarray(spec_uint8).convert("RGB")
        if processor:
            image = processor(images=image, return_tensors='pt')
        return image
    except LibrosaError as e:
        logger.error(f"Ошибка {e.__class__.__name__}: {e}")
        raise
    except Exception as e:
        logger.error(f"Общая ошибка {e.__class__.__name__}: {e}")
        raise


def spec_to_image(spec, processor=None):
    """Конвертирует любую спектрограмму (мел или CQT) в PIL Image."""
    spec_min, spec_max = spec.min(), spec.max()
    spec_scaled = 255 * (spec - spec_min) / (spec_max - spec_min + 1e-6)
    spec_uint8 = spec_scaled.astype(np.uint8)
    image = Image.fromarray(spec_uint8).convert("RGB")
    if processor:
        image = processor(images=image, return_tensors='pt')
    return image


def get_audio_metrics(y, sr):
    duration = librosa.get_duration(y=y, sr=sr)
    rms_mean = np.mean(librosa.feature.rms(y=y))
    peak_level = np.max(np.abs(y))
    zcr_mean = np.mean(librosa.feature.zero_crossing_rate(y))
    bandwidth_mean = np.mean(librosa.feature.spectral_bandwidth(y=y, sr=sr))
    rolloff_mean = np.mean(librosa.feature.spectral_rolloff(y=y, sr=sr, roll_percent=0.85))

    return {
        "file_info": {
            "sample_rate": sr,
            "duration_sec": round(duration, 2)
        },
        "deep_analysis": {
            "rms_level": round(float(rms_mean), 4),
            "peak_level": round(float(peak_level), 4),
            "spectral_bandwidth": round(float(bandwidth_mean), 2),
            "spectral_rolloff": round(float(rolloff_mean), 2),
            "zcr": round(float(zcr_mean), 4)
        }
    }


def aggregate_predictions(predictions, y, sr, th=0.2):
    total = len(predictions)
    defects = [p for p in predictions if p['defect']]
    defect_rate = len(defects) / total if total > 0 else 0
    avg_conf = float(np.mean([p['confidence'] for p in predictions]))

    return {
        'label': int(defect_rate > th),
        'defect': defect_rate > th,
        'confidence': round(avg_conf, 3),
        'defect_rate': round(defect_rate, 3),
        'total_notes': total,
        'defect_notes': len(defects),
        'notes': predictions,
        'metrics': get_audio_metrics(y, sr)
    }


def get_cents_deviation(segments: list[dict]) -> list[dict | None]:
    if not segments:
        return []

    sr = segments[0]["sr"]

    # Явное приведение каждого сегмента к float32 numpy → tensor
    ys = [
        torch.from_numpy(np.ascontiguousarray(seg["y"], dtype=np.float32))
        for seg in segments
    ]

    lengths = [y.shape[0] for y in ys]
    max_len = max(lengths)

    # Паддинг каждого тензора до max_len
    padded_list = [
        F.pad(y, (0, max_len - y.shape[0]))
        for y in ys
    ]

    # Проверка что все одинаковой длины перед stack
    assert all(t.shape[0] == max_len for t in padded_list), \
        f"Паддинг не сработал: {[t.shape for t in padded_list]}"

    padded = torch.stack(padded_list)  # (B, T)

    frequency, periodicity = torchcrepe.predict(
        padded,
        sr,
        hop_length=256,
        fmin=50,
        fmax=2000,
        model='full',
        return_periodicity=True,
        batch_size=len(segments),
    )

    hop = 256
    valid_frames = [math.ceil(l / hop) for l in lengths]

    results = []
    for i, n_frames in enumerate(valid_frames):
        freq_i = frequency[i, :n_frames]
        period_i = periodicity[i, :n_frames]

        voiced = period_i > 0.5
        freq_voiced = freq_i[voiced]

        if freq_voiced.numel() == 0:
            results.append(None)
            continue

        f0 = freq_voiced.median().item()
        midi = 69 + 12 * np.log2(f0 / 440.0)
        f_ref = 440.0 * 2 ** ((round(midi) - 69) / 12)
        cents = 1200 * np.log2(f0 / f_ref)

        results.append({"cents": cents, "periodicity": period_i[voiced].mean().item()})

    return results


def classify_tuning(cents, threshold=20) -> (str, int):
    if cents is None:
        label = -1
    elif abs(cents) < threshold:
        label = 0
    elif cents < -threshold:
        label = 1  # Недотянуто
    else:
        label = 2  # Перетянуто
    return {
        "label": label,
        "label_name": label_map.get(label)
    }
