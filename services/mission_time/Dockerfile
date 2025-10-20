FROM python:3.11-slim

WORKDIR /app

# Install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY src/ .

# Default mission file mount point
VOLUME ["/app/mission.yaml"]

CMD ["python", "main.py"]
