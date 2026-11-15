# Offline pilot image. The default command validates config and exits.
FROM python:3.13-slim@sha256:e48f59cdba69a3cbd9ed2cf0f348d90d45a8d350d98134cf1070bc106ee9ed90 AS dependencies
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 \
    HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 YOLO_CONFIG_DIR=/tmp/ultralytics \
    YOLO_AUTOINSTALL=false OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
RUN apt-get update && apt-get upgrade -y \
    && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 libgomp1 \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements-lock-linux.txt ./
RUN python -m pip install pip==26.3 \
    && python -m pip install --require-hashes -r requirements-lock-linux.txt \
    && python -m pip check
COPY coffee_ops/ ./coffee_ops/
COPY config/example.json ./config/example.json
COPY models/metadata.example.json ./models/metadata.example.json
COPY schemas/ ./schemas/
RUN useradd --uid 10001 --create-home coffee && mkdir /app/var && chown coffee:coffee /app/var
FROM dependencies AS test
COPY requirements-dev.txt ./
RUN python -m pip install -r requirements-dev.txt && python -m pip check
COPY tests/ ./tests/
COPY scripts/ ./scripts/
COPY notebooks/cafe_model_benchmark.ipynb ./notebooks/cafe_model_benchmark.ipynb
COPY README.md ./README.md
USER 10001:10001
CMD ["python", "-m", "unittest", "discover", "-s", "tests", "-v"]

FROM test AS video-test
USER root
COPY requirements-video.txt ./
RUN python -m pip install -r requirements-video.txt && python -m pip check
USER 10001:10001

FROM dependencies AS runtime
# pip/ensurepip are build tools, not application dependencies. Keep setuptools,
# which Torch declares. Do not alter third-party vendored code by hand.
RUN python -m pip uninstall -y pip \
    && rm -rf /usr/local/lib/python3.13/ensurepip
USER 10001:10001
CMD ["python", "-m", "coffee_ops", "validate-config"]

FROM runtime AS production
