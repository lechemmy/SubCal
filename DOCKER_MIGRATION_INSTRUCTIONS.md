# Docker Migration Instructions

## Issue: Missing `is_default` column in Currency table

If you're encountering the following error when accessing the settings page in your Docker installation:

```
OperationalError at /settings/
no such column: subscriptions_currency.is_default
```

This is because a database migration needs to be applied to add the `is_default` field to the Currency model.

## Solution

There are two ways to resolve this issue:

### Option 1: Apply the migration in the running container (Recommended)

This option preserves your existing data.

1. Find your running Docker container:
   ```bash
   docker ps
   ```

2. Connect to the container (replace `<container_id>` with your actual container ID or name):
   ```bash
   docker exec -it <container_id> bash
   ```

3. Run the migration command inside the container:
   ```bash
   python manage.py migrate
   ```

4. Run the updated script to set default currencies:
   ```bash
   python create_default_currencies.py
   ```

5. Exit the container:
   ```bash
   exit
   ```

### Option 2: Rebuild the Docker image and recreate the container

This option will reset your database to its initial state, losing any data you've added.

1. Stop the running container:
   ```bash
   docker-compose down
   ```

2. Remove the volume containing the database:
   ```bash
   docker volume rm subcal_sqlite_data
   ```

3. Rebuild and start the container:
   ```bash
   docker-compose up --build -d
   ```

## Preventing this issue in the future

To prevent this issue from happening again when you make model changes, consider modifying your Docker setup to run migrations on container start, not just during image build.

You can do this by creating a startup script that runs migrations before starting the application, or by using Docker Compose's `command` option to override the default command and run migrations first.

Example `docker-compose.yml` modification:

```yaml
services:
  web:
    build: .
    command: >
      bash -c "python manage.py migrate &&
               python create_default_categories.py &&
               python create_default_currencies.py &&
               gunicorn --bind 0.0.0.0:8000 SubCal.wsgi:application"
    # ... rest of your configuration
```

This ensures that migrations are applied every time the container starts, keeping your database schema in sync with your models.
