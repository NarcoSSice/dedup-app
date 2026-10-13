FROM python:3.11-slim AS deps
RUN pip install --no-cache-dir poetry==2.2.1
WORKDIR /backend
COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.in-project true \
 && poetry install --only main --no-root --no-interaction \
 && rm -rf /root/.cache

FROM python:3.11-slim
WORKDIR /backend
ENV PATH=/backend/.venv/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/backend/app \
    MODEL_PATH=/backend/dedup_model/sscd.torchscript.pt
COPY --from=deps /backend/.venv /backend/.venv
# model baked into the image: containers start offline, workers scale instantly
ADD https://dl.fbaipublicfiles.com/sscd-copy-detection/sscd_disc_mixup.torchscript.pt /backend/dedup_model/sscd.torchscript.pt
COPY app ./app
EXPOSE 8000
CMD ["python", "app/main.py"]
