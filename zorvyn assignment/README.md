# Finance Data Processing and Access Control Backend
Backend assignment implementation for finance record management, dashboard analytics, and role-based access control.

## Tech stack
- Python 3.10
- FastAPI
- SQLite (persistent local file database)
- Pytest (API tests)

## What is implemented
- User and role management with active or inactive status
- Mock token-based authentication (`/auth/login`)
- Role-based access control enforced in backend dependencies
- Financial records CRUD with filtering by:
  - `type`
  - `category`
  - `date_from` and `date_to`
- Dashboard summary API providing:
  - total income
  - total expenses
  - net balance
  - category-wise totals
  - recent activity
  - monthly trends
- Input validation through Pydantic schemas
- Consistent HTTP errors for unauthorized or invalid operations
- Automated tests for access control and aggregation behavior

## Role behavior
- `viewer`
  - can login
  - can access dashboard summary
  - cannot read or modify records
  - cannot manage users
- `analyst`
  - can login
  - can read records
  - can access dashboard summary
  - cannot create, update, or delete records
  - cannot manage users
- `admin`
  - full access to users and records
  - can access dashboard summary

## Default admin
On first startup, a default admin user is created:
- username: `admin`
- password: `admin123`

## Project structure
- `app/main.py` - FastAPI app and route wiring
- `app/database.py` - SQLite connection and schema initialization
- `app/crud.py` - Data access and analytics queries
- `app/dependencies.py` - authentication and RBAC guards
- `app/routers/` - route modules
- `app/schemas.py` - request and response validation models
- `tests/` - pytest API tests

## Setup and run
From `zorvyn assignment`:

1. Create virtual environment:
   - `py -m venv .venv`
2. Activate virtual environment:
   - PowerShell: `.venv\\Scripts\\Activate.ps1`
3. Install dependencies:
   - `py -m pip install -r requirements.txt`
4. Run API:
   - `py -m uvicorn app.main:app --reload`

Swagger docs will be available at:
- `http://127.0.0.1:8000/docs`

## Environment variable
- `FINANCE_DB_PATH` (optional): custom SQLite file path
- If not set, the API uses `finance.db` in the project root.

## Main API endpoints
### Authentication
- `POST /auth/login`
- `POST /auth/logout`
- `GET /auth/me`

### Users (admin only)
- `POST /users`
- `GET /users`
- `GET /users/{user_id}`
- `PATCH /users/{user_id}`
- `DELETE /users/{user_id}`

### Financial records
- `POST /records` (admin only)
- `GET /records` (analyst, admin)
- `GET /records/{record_id}` (analyst, admin)
- `PATCH /records/{record_id}` (admin only)
- `DELETE /records/{record_id}` (admin only)

### Dashboard
- `GET /dashboard/summary` (viewer, analyst, admin)
  - optional query params: `date_from`, `date_to`

## Running tests
- `py -m pytest`

## Assumptions and tradeoffs
- Authentication is mock token-based and stored in memory for assignment simplicity.
- Passwords are SHA-256 hashed for basic safety, but a production system should use stronger password hashing (for example, `bcrypt` or `argon2`).
- SQLite is used to keep setup simple and portable.
- Tokens reset when the server restarts.
- A default admin user is seeded automatically to make local evaluation quick.
