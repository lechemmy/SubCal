# SubCal - Subscription Calendar Manager

SubCal is a web application built with Django that helps you track and manage your subscriptions. Keep tabs on your recurring payments, view them in a calendar format, and never miss a renewal date again.

## Features

- **Subscription Management**: Add, edit, and delete subscription details including name, cost, renewal period, and more
- **Calendar View**: Visualize your subscriptions in a calendar format to see when payments are due
- **Day View**: Detailed view of subscriptions due on a specific day
- **Categorization**: Organize subscriptions by custom categories
- **Multi-Currency Support**: Track subscriptions in different currencies (USD, GBP, EUR)
- **Flexible Renewal Periods**: Support for weekly, monthly, and yearly subscription cycles

## Technologies Used

- Django 4.0+
- Python 3
- SQLite (default database)
- Python-dateutil for date manipulation
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

2. Build and start the Docker container:
   ```
   docker-compose up -d
   ```

3. Access the application at http://localhost:8000/

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
   - Renewal period (weekly, monthly, yearly)
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
