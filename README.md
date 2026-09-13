# Note\* **The system is still in development phase**

# **You can view the development branch to see upcoming features**

## MIS EVENT NEEDS MONITORING SYSTEM

Members:

- Enciso Jirho
- Christian Gabriel Pagulayan
- Maniago Raiyyan

## NEW FEATURES ADDED

**The API can now allow or disallow users to access information:**

- any user can regiter(create an account)
- list or delete users (via admin only)
- retrieve specific info, update/partial_update(update needs full info while partial update only updates a specific value)(via admin/owner only)
- any user can get the list of college, organization, department, and item but only the admin can create

**you can see the provided links on the very bottom to check how to access each via URL, the new features were tested using Hoppscotch**

### Note: Update and Delete(together with events, event_needs, and needs)features: In progress.

## Documentations:

<table align="center">
  <tr>
    <td><img width="100%" alt="acc1" src="https://github.com/user-attachments/assets/8b152bbf-d393-414a-8dbd-675ba8ab11f9" /></td>
    <td><img width="100%" alt="acc2" src="https://github.com/user-attachments/assets/179cfc1b-903b-4be6-9730-592bca6e2d70" /></td>
    <td><img width="100%" alt="acc3" src="https://github.com/user-attachments/assets/da3c59b8-caf2-45b1-aebf-43bca2b27919" /></td>
  </tr>
  <tr>
    <td><img width="100%" alt="acc4" src="https://github.com/user-attachments/assets/30e74650-2f71-4258-8a68-14f30935d3ee" /></td>
    <td><img width="100%" alt="acc5" src="https://github.com/user-attachments/assets/eff3e429-67c7-46f1-a1db-bbc94fa35732" /></td>
    <td><img width="100%" alt="acc6" src="https://github.com/user-attachments/assets/d26a40c4-ce57-4efc-9429-0c52dc1f9b50" /></td>
  </tr>
</table>

## Entity Relationship(ER) Diagram

---

## <img width="779" height="912" alt="ERdiagram" src="https://github.com/user-attachments/assets/de32a3e8-df0b-4e19-b064-46f5073ee045" />

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
http://localhost:8000/api/needs/
http://localhost:8000/api/event-needs/

http://localhost:8000/api/organization-list/
http://localhost:8000/api/organization-create/

http://localhost:8000/api/department-list/
http://localhost:8000/api/department-create/

http://localhost:8000/api/college-list/
http://localhost:8000/api/college-create/

http://localhost:8000/api/items-list/
http://localhost:8000/api/items-create/

http://localhost:8000/api/login/
http://localhost:8000/api/register/
http://localhost:8000/api/account-lists/
http://localhost:8000/api/profile/username/
http://localhost:8000/api/profile/edit/username/
http://localhost:8000/api/profile/edit-field/username/
http://localhost:8000/api/profile/delete/username/
```
