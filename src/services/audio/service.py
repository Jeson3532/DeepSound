from transformers import ConvNextImageProcessor, ConvNextForImageClassification
import torch
import pyprojroot as ppr
from peft import PeftModel
from src.services.audio.extract import get_mel_spec, load_audio, get_audio_metrics, aggregate_predictions, \
    segment_audio, get_cents_deviation, classify_tuning
import asyncio
from concurrent.futures import ThreadPoolExecutor
from src.exceptions import NoAudioSegments
import librosa
import io

models_path = ppr.here() / 'models'
model_name = 'facebook/convnext-base-224-22k-1k'
checkpoint_path = models_path / 'convnext-finetuned-cqt-2'

DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'


def load_convnext_model(base_model_path: str, model_path: str):
    model = ConvNextForImageClassification.from_pretrained(
        base_model_path,
        num_labels=2,
        id2label={
            0: "normal",
            1: "defect"
        },
        label2id={
            "normal": 0,
            "defect": 1
        },
        ignore_mismatched_sizes=True
    )
    return PeftModel.from_pretrained(model, model_path)


def load_convnext_processor(path: str):
    return ConvNextImageProcessor.from_pretrained(path)


class AudioService:
    def __init__(self,
                 model_path: str = checkpoint_path,
                 base_model_name: str = model_name
                 ):
        # self.model = load_convnext_model(base_model_name, model_path)
        # self.processor = load_convnext_processor(base_model_name)
        self.executor = ThreadPoolExecutor(max_workers=2)

        #self.model.to(DEVICE)
        #self.model.eval()

    def process_analyze(self, audio: bytes | str):
        y, sr = load_audio(audio)

        segments = segment_audio(y, sr)
        if not segments:
            raise NoAudioSegments("Ноты не обнаружены в аудио")

        # Батчевый проход — один вызов torchcrepe на все сегменты
        batch_results = get_cents_deviation(segments)

        predictions = []
        for seg, result in zip(segments, batch_results):
            if result is None:
                continue

            response = classify_tuning(result["cents"])
            label = response.get("label")

            predictions.append({
                "start": seg["start"],
                "duration": seg["duration"],
                "label": label,
                "confidence": result["periodicity"],
                "defect": label in [1, 2],
            })

        return aggregate_predictions(predictions, y, sr)

    async def analyze(self, audio: bytes | str):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, self.process_analyze, audio)


# import pyprojroot as ppr
# from pathlib import Path
#
# root_path = ppr.here()
# file_path = Path(root_path) / 'test_files' / '13.m4a'
# a = AudioService()
# with open(file_path, 'rb') as f:
#     file_b = f.read()
# result = a.process_analyze(file_b)
# print(result)
