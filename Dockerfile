# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory inside the container
WORKDIR /app

# Install pip dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy the rest of the project
COPY . .

# Expose the port Django will run on
EXPOSE 8000

# Run gunicorn server
CMD ["sh", "-c", "python manage.py makemigrations && python manage.py migrate && gunicorn sme_backend.wsgi:application --bind 0.0.0.0:8000"]
