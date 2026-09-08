# Note* **The system is still in development phase**
# **You can view the development branch to see upcoming features**

## MIS EVENT NEEDS MONITORING SYSTEM

Members:
- Enciso Jirho
- Christian Gabriel Pagulayan
- Maniago Raiyyan

## Entity Relationship(ER) Diagram
---
<img width="779" height="912" alt="ERdiagram" src="https://github.com/user-attachments/assets/de32a3e8-df0b-4e19-b064-46f5073ee045" />
---

## Overview
This monitoring system is intended to help systematically manage and view upcoming or passed events for the MIS Office.

### Prerequisites

- [Python 3.12+](https://www.python.org/downloads/)
- [Git](https://git-scm.com/)
- [PostgreSQL](https://www.postgresql.org/)
- [pgAdmin](https://www.pgadmin.org/)

### Installation & Setup

1. **Clone the Repository**
   ```bash
   git clone https://github.com/Jirho-BE/MIS-Event-Needs-Monitoring-System.git
   cd MIS-Event-Needs-Monitoring-System
   ```

2. **Create and Activate Virtual Environment**
   - **Windows (PowerShell)**:
     ```powershell
     python -m venv .venv
     .venv\Scripts\Activate.ps1
     ```
   - **Linux / macOS**:
     ```bash
     python3 -m venv .venv
     source .venv/bin/activate
     ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

### Database Setup and Migrations

1. Open pgAdmin, create a database "mis_monitoring"
2. Go to server folder inside the cloned repo
3. Edit settings.py
```python
DATABASES = {
    'default': {
		'ENGINE': 'django.db.backends.postgresql',
		'NAME': 'mis_monitoring', #change this to the database name you set at pgAdmin if you did not create the "mis_monitoring"
		'USER': 'postgres', #Change this to your username
		'PASSWORD': 'postgres', #Change this to your password
		'HOST': 'localhost',
		'PORT': '5432'
	}
}
```
4. Now make migrations then migrate
```bash
python manage.py makemigrations
python manage.py migrate
```
### Running the server
   ```bash
   python manage.py runserver
   ```
### Paste onto a browser of choice (any link)
```url
http://localhost:8000/api/events/
http://localhost:8000/api/organization/
http://localhost:8000/api/department/
http://localhost:8000/api/college/
http://localhost:8000/api/items/
http://localhost:8000/api/needs/
http://localhost:8000/api/event-needs/

http://localhost:8000/api/accounts/
http://localhost:8000/api/login/
http://localhost:8000/api/register/
```
