FROM python:3.9-slim

WORKDIR /app

ENV PYTHONPATH=/app

COPY requirements.txt requirements.txt

# Install uv
RUN pip install uv

# Install dependencies using uv
RUN uv pip install -r requirements.txt --system

COPY . .

EXPOSE 80

CMD ["python", "app.py"]