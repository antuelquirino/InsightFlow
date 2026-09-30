# The InsightFlow API for Cloud Run. Only the API and its runtime dependencies;
# the generator, dbt and the web app stay out of the image.
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8080 \
    ASK_LOG_PATH=-

WORKDIR /app

COPY api/requirements.txt api/requirements.txt
RUN pip install -r api/requirements.txt

COPY api/ api/

# Run as a non-root user.
RUN useradd --create-home insightflow
USER insightflow

# --proxy-headers: Cloud Run sits behind Google's front end, so the client IP
# (used by the /ask rate limit) comes from X-Forwarded-For.
CMD exec uvicorn api.main:app --host 0.0.0.0 --port "${PORT}" --proxy-headers --forwarded-allow-ips="*"
