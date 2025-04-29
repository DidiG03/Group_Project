# Health Check Application

A comprehensive Django web application for project management and health tracking in organizations. This application allows companies to manage departments, teams, projects, and track the health status of various projects.

## Features

- **User Authentication**: Register, login, and user approval system
- **Company Management**: Create and manage company profiles
- **Department and Team Organization**: Organize employees into departments and teams
- **Project Management**: Create, track, and monitor projects with health status indicators
- **Todo Lists**: Create and manage to-do lists and items
- **Comment System**: Leave comments on projects and reply to comments
- **Role-Based Access**: Different access levels for admins and employees
- **Profile Management**: User profiles with technical roles and department/team affiliations
- **Team Password Protection**: Team leaders can set passwords for their teams, allowing members to join directly

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Virtual environment tool (virtualenv or venv)

## Installation Guide

### 1. Install Python

#### Windows
1. Download the latest Python version from [python.org](https://www.python.org/downloads/windows/)
2. Run the installer and check "Add Python to PATH" during installation
3. Verify installation by opening Command Prompt and typing:
   ```
   python --version
   ```

#### macOS
1. Install Homebrew (if not already installed):
   ```
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```
2. Install Python using Homebrew:
   ```
   brew install python
   ```
3. Verify installation:
   ```
   python3 --version
   ```

#### Linux (Ubuntu/Debian)
1. Update package index:
   ```
   sudo apt update
   ```
2. Install Python:
   ```
   sudo apt install python3 python3-pip
   ```
3. Verify installation:
   ```
   python3 --version
   ```

### 2. Clone the Repository

```
git clone https://github.com/yourusername/Group_Project.git
cd Group_Project
```

### 3. Set Up Virtual Environment in VSCode

1. Open the project folder in VSCode
2. Open the VSCode terminal (Terminal > New Terminal)
3. Create a virtual environment:

   ```
   # On Windows
   python -m venv venv

   # On macOS/Linux
   python3 -m venv venv
   ```

4. Activate the virtual environment:

   ```
   # On Windows
   venv\Scripts\activate

   # On macOS/Linux
   source venv/bin/activate
   ```

   You should see `(venv)` at the beginning of your terminal prompt, indicating that the virtual environment is active.

### 4. Install Dependencies

Create a `requirements.txt` file in the root directory with the following content:

```
Django>=5.0.0
django-crispy-forms>=2.0
crispy-bootstrap4>=2022.1
Pillow>=10.0.0
```

Then install the dependencies:

```
pip install -r requirements.txt
```

### 5. Database Setup

Run migrations to set up the database:

```
python manage.py migrate
```

### 6. Create Superuser (Admin)

Create an admin user to access the Django admin interface:

```
python manage.py createsuperuser
```

Follow the prompts to set up your admin username, email, and password.

### 7. Run the Development Server

Start the Django development server:

```
python manage.py runserver
```

The application will be available at http://127.0.0.1:8000/

## Usage

1. Access the admin interface at http://127.0.0.1:8000/admin/ using your superuser credentials
2. Create departments, teams, and set up the organizational structure
3. Register new users who can then create company profiles or join existing ones
4. Manage projects, track their health status, and organize tasks

### Team Management
- **Team Leaders** can set passwords for their teams in the Team Leader Dashboard
- **Team Members** can join teams directly by using the team code and password from their Settings page
- **Team Join Requests** can be submitted for teams that don't use password protection
- **Team Leaders** can approve or reject join requests from their dashboard

## Project Structure

- `HealthCheckApp/`: Main Django project settings
- `main/`: Core application functionality
  - Project management
  - Department and team management
  - Todo list functionality
- `register/`: User authentication and registration
  - User profiles
  - Company registration


## Contributors

- Sefrid Kapllani
- Jakub Raczkiewicz
- Abulai Danfa
- Fattouh Mohammed
