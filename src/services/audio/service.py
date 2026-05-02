from transformers import ConvNextImageProcessor, ConvNextForImageClassification
import torch
import pyprojroot as ppr
from peft import PeftModel
from src.services.audio.extract import get_mel_spec, load_audio, get_audio_metrics, aggregate_predictions, segment_audio, get_cqt
import asyncio
from concurrent.futures import ThreadPoolExecutor
from src.exceptions import NoAudioSegments

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
        self.model = load_convnext_model(base_model_name, model_path)
        self.processor = load_convnext_processor(base_model_name)
        self.executor = ThreadPoolExecutor(max_workers=2)

        self.model.to(DEVICE)
        self.model.eval()

    def process_analyze(self, audio: bytes | str):
        y, sr = load_audio(audio)

        # Детектируем ноты
        segments = segment_audio(y, sr)

        if not segments:
            raise NoAudioSegments("Ноты не обнаружены в аудио")

        # Предсказываем для каждого сегмента
        predictions = []
        for seg in segments:
            inputs = get_cqt(seg['y'], seg['sr'], processor=self.processor)
            inputs = {k: v.to(DEVICE) for k, v in inputs.items()}

            with torch.no_grad():
                logits = self.model(**inputs).logits
                probs = torch.softmax(logits, dim=-1)[0]

            label = int(torch.argmax(probs).item())
            conf = float(probs[label].item())

            predictions.append({
                'start': seg['start'],
                'duration': seg['duration'],
                'label': label,
                'confidence': conf,
                'defect': label == 1
            })

        # Агрегация
        return aggregate_predictions(predictions, y, sr)


    async def analyze(self, audio: bytes | str):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, self.process_analyze, audio)
