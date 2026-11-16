FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# The code imports itself as the perfima package, so it lives in /app/perfima and runs from /app
WORKDIR /app

COPY requirements.txt /app/perfima/requirements.txt
RUN pip install --no-cache-dir -r /app/perfima/requirements.txt

COPY . /app/perfima

RUN useradd --create-home perfima && chown perfima /app
USER perfima

EXPOSE 8000
CMD ["uvicorn", "perfima.main:app", "--host", "0.0.0.0", "--port", "8000"]
