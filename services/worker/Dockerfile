FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN pip install --no-cache-dir --upgrade pip

# See services/api/Dockerfile for rationale.
RUN pip install --no-cache-dir pydantic

COPY services/api/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY services/api /app

CMD ["bash", "/app/scripts/worker-entrypoint.sh"]
