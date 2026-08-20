FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml ./
# Longer timeouts: flaky/slow links to files.pythonhosted.org often abort local builds.
RUN pip install --no-cache-dir --default-timeout=120 --retries=5 .

COPY app ./app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

