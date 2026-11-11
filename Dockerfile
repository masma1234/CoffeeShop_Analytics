# Resolve and record the base digest before a release. Local/CI verification only;
# this image does not turn the loopback pilot server into a hosted web service.
FROM python:3.13-slim@sha256:e48f59cdba69a3cbd9ed2cf0f348d90d45a8d350d98134cf1070bc106ee9ed90 AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 \
    HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 YOLO_CONFIG_DIR=/tmp/ultralytics \
    OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
RUN apt-get update && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 libgomp1 \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt ./
RUN python -m pip install torch==2.9.0 torchvision==0.24.0 --index-url https://download.pytorch.org/whl/cpu \
    && python -m pip install -r requirements.txt && python -m pip check
COPY coffee_ops/ ./coffee_ops/
COPY config/example.json ./config/example.json
COPY models/metadata.example.json ./models/metadata.example.json
COPY schemas/ ./schemas/
RUN useradd --uid 10001 --create-home coffee && mkdir /app/var && chown coffee:coffee /app/var
USER 10001:10001
CMD ["python", "-m", "coffee_ops", "validate-config"]

FROM runtime AS test
COPY tests/ ./tests/
COPY scripts/ ./scripts/
COPY notebooks/cafe_model_benchmark.ipynb ./notebooks/cafe_model_benchmark.ipynb
COPY README.md ./README.md
CMD ["python", "-m", "unittest", "discover", "-s", "tests", "-v"]

FROM test AS video-test
USER root
COPY requirements-video.txt ./
RUN python -m pip install -r requirements-video.txt && python -m pip check
USER 10001:10001

FROM runtime AS production
