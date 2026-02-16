# ─────────────────────────────────────────────────
# PromptTriage Backend — Production Docker Build
# ─────────────────────────────────────────────────
# Slim Python image, non-root user, Cloud Run ready.

FROM python:3.11-slim AS builder

WORKDIR /app

# Install build deps for compiled packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ─── Production stage ───
FROM python:3.11-slim

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application code (only what's needed for the API)
COPY app/ ./app/

# Non-root user for security
RUN addgroup --system --gid 1001 appuser \
    && adduser --system --uid 1001 --ingroup appuser appuser
USER appuser

# Cloud Run injects PORT env var (default 8080)
ENV PORT=8080
EXPOSE 8080

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
