# ==========================================================
#  Music Player Bot  --  Railway / Docker
#  Base: Debian slim (سبک، پایدار، بیلد سریع)
#  اگر Kali می‌خواهید، از Dockerfile.kali استفاده کنید
# ==========================================================
FROM python:3.11-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DEBIAN_FRONTEND=noninteractive \
    TZ=Asia/Tehran

# ffmpeg برای PyTgCalls الزامی است
# psmisc شامل fuser است (اگر به پچ تکیه نکردید)
RUN apt-get update && apt-get install -y --no-install-recommends \
        ffmpeg \
        psmisc \
        curl \
        ca-certificates \
        tzdata \
        fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY . .

# مسیرهایی که باید روی Volume باشند
RUN mkdir -p /app/data /app/downloads
VOLUME ["/app/data"]

# بررسی سالم بودن ffmpeg در زمان بیلد
RUN ffmpeg -version > /dev/null && echo "ffmpeg OK"

CMD ["python3", "main.py"]
