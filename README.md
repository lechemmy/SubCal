# This is an AI project written by Junie in PyCharm. It should work but the docker install currently may have errors. 

# SubCal - Subscription Calendar Manager

SubCal is a web application built with Django that helps you track and manage your subscriptions. Keep tabs on your recurring payments, view them in a calendar format, and never miss a renewal date again.

## Features

- **Subscription Management**: Add, edit, and delete subscription details including name, cost, renewal period, and more
- **Calendar View**: Visualize your subscriptions in a calendar format to see when payments are due
- **Day View**: Detailed view of subscriptions due on a specific day
- **Categorization**: Organize subscriptions by custom categories
- **Multi-Currency Support**: Track subscriptions in different currencies (USD, GBP, EUR)
- **Flexible Renewal Periods**: Support for weekly, monthly, quarterly, yearly, and biennial subscription cycles

## Technologies Used

- Django 4.0+
- Python 3
- SQLite (default database)
- Python-dateutil for date manipulation
- Python-dotenv for environment variable management
- HTML/CSS for frontend

## Installation

### Option 1: Standard Installation

1. Clone the repository:
   ```
   git clone https://github.com/lechemmy/SubCal.git
   cd SubCal
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows, use: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Run migrations:
   ```
   python manage.py migrate
   ```

5. Create default categories and currencies (optional):
   ```
   python create_default_categories.py
   python create_default_currencies.py
   ```

6. Start the development server:
   ```
   python manage.py runserver
   ```

7. Access the application at http://127.0.0.1:8000/

### Option 2: Docker Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/SubCal.git
   cd SubCal
   ```

2. Configure Docker environment (optional):
   ```
   cp .env.docker.example .env.docker
   ```
   Edit `.env.docker` to set your environment variables, including `ALLOWED_HOSTS`.

3. Build and start the Docker container:
   ```
   docker-compose up -d
   ```

4. Access the application at http://localhost:8001/

#### Configuring ALLOWED_HOSTS for Docker

The Docker setup uses the `.env.docker` file to configure environment variables, including `ALLOWED_HOSTS`. By default, it's set to `localhost,127.0.0.1,*` which allows any host to access the application.

For production, it's recommended to set `ALLOWED_HOSTS` to a specific list of domains:

```
# In .env.docker
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
```

You can also override this setting when starting the container:

```
ALLOWED_HOSTS=yourdomain.com docker-compose up -d
```

#### Understanding Docker Networking

When running SubCal in Docker, you might notice that the Docker container has a different IP address than your host machine (e.g., your Raspberry Pi). For example, if your Pi has an IP address of 192.168.35.7, the Docker container might have an IP address like 192.168.96.2.

This is normal and by design:

1. **Docker creates its own network**: Docker sets up a virtual network for containers that's separate from your host network.
2. **Network isolation**: This provides security benefits by isolating container traffic from the host.
3. **Port mapping**: The application is still accessible from your host IP address through the mapped port (8001).

To access the application:
- From the same machine: http://localhost:8001/
- From other devices on your network: http://[YOUR_PI_IP]:8001/ (e.g., http://192.168.35.7:8001/)

The Docker container's internal IP address (192.168.96.2) is only used for communication between containers and isn't directly accessible from outside the Docker network.

## Environment Configuration

SubCal uses environment variables for configuration, which can be set in a `.env` file at the project root. This allows for different configurations between development and production environments.

### Setting Up Environment Variables

1. Copy the example environment file to create your own:
   ```
   cp .env.example .env
   ```

2. Edit the `.env` file to configure your environment:
   ```
   # Development environment (set to False in production)
   DEBUG=True

   # Secret key (generate a new one for production)
   SECRET_KEY=your-secret-key-here

   # Allowed hosts (comma-separated list)
   ALLOWED_HOSTS=localhost,127.0.0.1
   ```

3. For production environments, make sure to:
   - Set `DEBUG=False`
   - Generate a new secure `SECRET_KEY`
   - Set `ALLOWED_HOSTS` to your domain(s)

### Available Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| DEBUG | Enable debug mode | True |
| SECRET_KEY | Django secret key | Default insecure key |
| ALLOWED_HOSTS | Comma-separated list of allowed hosts | localhost,127.0.0.1 |
| DATABASE_DIR | Directory for SQLite database | Project root |
| STATIC_ROOT | Directory for collected static files | staticfiles/ |

#### Docker Commands

- Start the application:
  ```
  docker-compose up -d
  ```

- Stop the application:
  ```
  docker-compose down
  ```

- View logs:
  ```
  docker-compose logs -f
  ```

- Rebuild the container after changes:
  ```
  docker-compose up -d --build
  ```

## Usage

### Adding a Subscription

1. Navigate to the "Add Subscription" page
2. Fill in the subscription details:
   - Name
   - Category (optional)
   - Cost
   - Currency
   - Renewal period (weekly, monthly, quarterly, yearly, biennial)
   - Start date
   - Notes (optional)
3. Click "Save" to add the subscription

### Viewing Subscriptions

- **List View**: See all your subscriptions in a list format
- **Calendar View**: Visualize subscriptions in a monthly calendar
- **Day View**: Click on a specific day to see subscriptions due on that day

### Managing Categories and Currencies

- Access the settings page to add, edit, or delete categories and currencies

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is open source and available under the [MIT License](LICENSE).
