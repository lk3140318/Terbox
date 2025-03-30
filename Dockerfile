FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Ensure the database directory exists and is writable if needed
# RUN mkdir /data && chown <user>:<group> /data # Adjust user/group if needed

ENV TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}

# The database will be created inside the container's /app directory by default
CMD ["python", "bot.py"]
