FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 TZ=Asia/Tashkent
RUN apt-get update && apt-get install -y --no-install-recommends fonts-dejavu-core tzdata && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# SERVICE_ROLE=web — sayt (ochiq sahifa, admin panel, Mini App); bo'lmasa — Telegram bot.
# Railway'da bitta tasvirdan ikki xizmat shu bilan ajratiladi; docker-compose «command:» bilan baribir aniq beradi.
CMD ["sh", "-c", "if [ \"$SERVICE_ROLE\" = web ]; then exec python -m admin_site; else exec python bot.py; fi"]
