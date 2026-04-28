FROM python:3.12-slim

WORKDIR /deepsound

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "src.backend.entry:app", "--host", "0.0.0.0", "--port", "5000"]
