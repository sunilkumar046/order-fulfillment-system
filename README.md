Generic single-database configuration.Order Fulfillment & Inventory Management Platform
A REST API built with FastAPI for managing order fulfillment and inventory operations. The project is organized into routers, services, repositories, SQLAlchemy models, schemas, and database migrations.
Features
- User authentication with access and refresh token support
- Role-based access control and warehouse access dependencies
- Product categories and product catalog management
- Warehouse and inventory management
- Inventory transactions, reservations, and transfers
- Order creation and order-status history
- Return requests
- Notifications and audit logs
- Dashboard and reporting endpoints
- Centralized exception handling and request validation
- Database schema migrations with Alembic
- Automated tests with pytest
Technology Stack
- Python
- FastAPI
- SQLAlchemy
- PostgreSQL
- Alembic
- JWT-based authentication
- Pytest
Project Structure


order_fulfillment_system/
├── alembic/              # Database migration environment and revisions
├── app/
│   ├── core/             # Configuration, security, and exception handlers
│   ├── database/         # Database engine and base configuration
│   ├── dependencies/     # Authentication and warehouse dependencies
│   ├── models/           # SQLAlchemy models
│   ├── repositories/     # Data access layer
│   ├── routers/          # API endpoints
│   ├── schemas/          # Request and response schemas
│   ├── services/         # Business logic
│   └── utils/            # Utility scripts
├── tests/                # Automated tests
├── .env.example          # Example environment configuration
├── alembic.ini           # Alembic configuration
├── requirements.txt      # Python dependencies
└── README.md

Prerequisites
- Python 3.10 or newer (use the version supported by your installed dependencies)
- PostgreSQL
- Git

Setup and Run
1. Clone the repository
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd order_fulfillment_system
If you already have the project locally, open a terminal in the project directory instead.
2. Create and activate a virtual environment
Windows PowerShell:
python -m venv venv
.\venv\Scripts\Activate.ps1
If PowerShell blocks activation, you can use Command Prompt and run venv\Scripts\activate.bat, or follow your organization's PowerShell execution-policy guidance.
3. Install dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt
Make sure requirements.txt contains all runtime and development dependencies used by the project. If startup reports a missing package, add the appropriate package to the requirements file and install it.
4. Configure environment variables
Create a local .env file from the example:
Copy-Item .env.example .env
Edit .env and configure your local PostgreSQL connection and authentication settings. For example:
APP_NAME=Order Fulfillment & Inventory Management Platform
APP_VERSION=1.0.0
DEBUG=True
DATABASE_URL=postgresql+psycopg://<username>:<password>@localhost:5432/order_fulfillment_db
JWT_SECRET_KEY=<generate-a-long-random-secret>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
Create the order_fulfillment_db database in PostgreSQL (or use the database name configured in your DATABASE_URL). Replace every placeholder with your own local values. Never commit .env, database passwords, or real JWT secrets to GitHub.
5. Apply database migrations
With PostgreSQL running and DATABASE_URL configured, run:
alembic upgrade head
6. Start the API
uvicorn app.main:app --reload
The local API is normally available at http://127.0.0.1:8000.
API Documentation
Once the server is running, open:
- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc
- Root endpoint: http://127.0.0.1:8000/
- Health check: http://127.0.0.1:8000/health
Use Swagger UI to inspect available endpoints and try requests. Protected endpoints require the authentication credentials/token expected by the API.
Run Tests
From the project root, run:
pytest
Ensure your test environment and database settings are configured as required by the test suite.
Database Migrations
Create a new migration after changing models (review the generated migration before applying it):
alembic revision --autogenerate -m "describe your change"
alembic upgrade head
Security Notes
- Keep .env out of version control.
- Use a strong, randomly generated JWT_SECRET_KEY outside local development.
- Do not publish database credentials, access tokens, or other secrets in README files, screenshots, logs, or commits.
- Use production-appropriate settings before deploying the API.
License
No license has been specified. Add a LICENSE file if you intend to distribute this project under a particular license.
