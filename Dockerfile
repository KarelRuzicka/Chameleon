FROM python:3.13-slim

# Keep Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turn off buffering for real-time container logging
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Copy just the requirements first to leverage Docker cache
COPY requirements.txt .

# Install dependencies without storing cache to keep the image small
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "bot.py"]