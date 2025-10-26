FROM python:3.11-slim

WORKDIR /app

COPY scraper.py .

RUN pip install requests beautifulsoup4

CMD ["python", "scraper.py"]