FROM nvidia/cuda:12.6.2-runtime-ubuntu24.04

RUN apt-get update && apt-get install -y \
    python3.12 \
    python3-pip \
    python3.12-dev \
    libsndfile1 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# python 3.12
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.12 1 \
    && update-alternatives --set python3 /usr/bin/python3.12

WORKDIR /deepsound

COPY requirements.txt .

ENV PIP_BREAK_SYSTEM_PACKAGES=1
RUN pip3 install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu130
RUN pip3 install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "src.backend.entry:app", "--host", "0.0.0.0", "--port", "5000"]
