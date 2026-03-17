FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN pip install --no-cache-dir --upgrade pip

# Work around occasional resolver/index flakiness during bulk installs by
# installing pydantic in a dedicated layer first.
RUN pip install --no-cache-dir pydantic

COPY services/api/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY services/api /app

EXPOSE 8000

CMD ["bash", "/app/scripts/api-entrypoint.sh"]
