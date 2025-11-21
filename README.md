# Overtime & Attendance Management System

A modern web application built with Python Flask, SQLite, and Bootstrap 5.

## Features

- **User Authentication**: Secure registration and login.
- **Dashboard**: Visual statistics, charts, and quick actions.
- **Overtime Management**: Add and track overtime hours.
- **Attendance Tracking**: Mark daily attendance with status and time.
- **Profile Management**: Update salary and overtime rates.
- **Export**: Export data to Excel and PDF.

## Installation

1.  **Install Python**: Ensure Python is installed on your system.
2.  **Create a Virtual Environment** (Optional but recommended):
    ```bash
    python -m venv venv
    # Windows
    venv\Scripts\activate
    # Mac/Linux
    source venv/bin/activate
    ```
3.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## Running the Application

1.  Run the application:
    ```bash
    python run.py
    ```
2.  Open your browser and go to: `http://127.0.0.1:5000`

## Usage

1.  **Register** a new account.
2.  Go to **Profile** to set your Monthly Salary and Overtime Rate.
3.  Use **Add OT** to log overtime hours.
4.  Use **Attendance** to mark your daily status.
5.  View your **Dashboard** for insights and charts.
6.  **Export** your data using the buttons on the dashboard.

## Tech Stack

-   **Backend**: Python, Flask, SQLAlchemy, SQLite
-   **Frontend**: HTML5, Bootstrap 5, Chart.js
-   **Export**: Pandas, OpenPyXL, FPDF
