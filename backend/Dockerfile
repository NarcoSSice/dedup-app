FROM python:3.11-slim AS deps
WORKDIR /backend

RUN pip install --no-cache-dir poetry==2.2.1
COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.in-project true \
 && poetry install --only main --no-root --no-interaction


FROM python:3.11-slim
WORKDIR /backend

ADD https://dl.fbaipublicfiles.com/sscd-copy-detection/sscd_disc_mixup.torchscript.pt dedup_model/

COPY --from=deps /backend/.venv /backend/.venv
ENV PATH=/backend/.venv/bin:$PATH

COPY app ./app
ENV PYTHONUNBUFFERED=1

EXPOSE 8000
CMD ["python", "app/main.py"]
