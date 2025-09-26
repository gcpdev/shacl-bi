# SHACL-BI: Business Intelligence for Semantic Data Quality Management

## Project Overview

SHACL-BI (SHACL Business Intelligence) is a unified platform for semantic data quality management through AI-enhanced SHACL validation and interactive analytics. It integrates the PHOENIX project (formerly xpSHACL) with SHACL Dashboard to provide a comprehensive solution for working with SHACL.

## Architecture

The application is composed of three main components:

- **Backend**: A Python Flask application that provides a RESTful API for SHACL validation, violation management, and statistics.
- **Frontend**: A Vue.js single-page application that provides a user interface for interacting with the backend.
- **Database**: A Virtuoso triple store for storing SHACL validation reports and the violation knowledge graph.

## Running the Application

### Using Docker (Recommended)

This is the easiest way to run the application.

**Prerequisites:**

- Docker
- Docker Compose

**Steps:**

1.  Create a `.env` file in the root directory with the following content:

    ```
    OPENAI_API_KEY=your_openai_api_key
    ```

2.  Run the following command in the root directory:

    ```
    docker-compose up -d
    ```

3.  The application will be available at `http://localhost:8080`.

### Local Development

This is useful for developing and debugging the application.

**Prerequisites:**

- Python 3.11
- Node.js 18
- Virtuoso

**Backend:**

1.  Navigate to the `backend` directory.
2.  Create a virtual environment: `python -m venv venv`
3.  Activate the virtual environment: `venv\Scripts\activate` (on Windows) or `source venv/bin/activate` (on Linux/macOS).
4.  Install the dependencies: `pip install -r requirements.txt`
5.  Run the application from the root directory: `python run.py`

**Frontend:**

1.  Navigate to the `frontend` directory.
2.  Install the dependencies: `npm install`
3.  Run the development server: `npm run serve`

## API Endpoints

- `GET /api/`: A simple endpoint to check if the API is running.
- `POST /api/validate`: Validates a data graph against a shapes graph.
- `GET /api/violations`: Returns a list of all violations.
- `GET /api/violations/<violation_id>`: Returns the details of a specific violation.
- `GET /api/statistics`: Returns the total number of violations.
- `POST /api/admin/login`: Generates a JWT token for authentication.
- `POST /api/admin/load_ontology`: Loads the violation ontology into the database.

## Frontend Components

- `Validation.vue`: A form to upload data and shapes graphs for validation.
- `Violations.vue`: A table to display a list of violations with sorting.
- `ViolationDetails.vue`: A component to display the details of a specific violation.

