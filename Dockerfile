FROM python:3.12-slim

WORKDIR /app

# Install requirements
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy app code
COPY . .

# Expose port 7860 (HF default)
EXPOSE 7860

# Run SoulSync
CMD ["chainlit", "run", "app.py", "-h", "0.0.0.0", "-p", "7860"]
