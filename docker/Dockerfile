FROM python:3.14-slim AS base

LABEL maintainer="Telebot"
LABEL description="Telegram Search Bot with Credit System"

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gcc \
        g++ \
        && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Create logs directory
RUN mkdir -p /app/logs

# Copy source code
COPY . .

# Expose health check port
EXPOSE 8080

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python scripts/health_check.py || exit 1

# Run the bot
CMD ["python", "bot.py"]
