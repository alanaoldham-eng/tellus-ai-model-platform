FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml README.md ./
COPY services ./services
COPY prompts ./prompts
COPY docs ./docs
COPY LICENSES ./LICENSES

RUN pip install --no-cache-dir .

EXPOSE 8000

CMD ["uvicorn", "services.api.main:app", "--host", "0.0.0.0", "--port", "8000"]

