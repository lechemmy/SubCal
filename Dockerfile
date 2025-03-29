FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
# Fix requirements.txt (remove trailing % from python-dateutil line)
RUN sed -i 's/%$//' requirements.txt
# Install dependencies and gunicorn
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Copy project
COPY . .

# Run migrations and create default data
RUN python manage.py migrate
RUN python create_default_categories.py
RUN python create_default_currencies.py

# Collect static files
RUN mkdir -p /app/staticfiles
ENV STATIC_ROOT=/app/staticfiles
RUN python manage.py collectstatic --noinput

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBUG=False
ENV SECRET_KEY=your-secret-key-here
ENV ALLOWED_HOSTS=localhost,127.0.0.1

# Expose port
EXPOSE 8000

# Run the application
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "SubCal.wsgi:application"]
