from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import os

app = Flask(__name__)

DATABASE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "database.db"
)

app.secret_key = os.environ.get(
    "SECRET_KEY",
    "change-this-secret-key-before-deployment"
)

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")

app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"


# =====================================
# DATABASE CONNECTION
# =====================================

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# =====================================
# CREATE / UPDATE DATABASE
# =====================================

def init_db():
    conn = get_db_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS survey_responses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            climate_change TEXT,
            local_impact TEXT,
            extreme_weather TEXT,
            waste_segregation TEXT,
            rainwater_energy TEXT,
            main_problem TEXT,
            information_source TEXT,
            tree_drive TEXT,
            respondent_name TEXT,
            respondent_age INTEGER
        )
    """)

    existing_columns = {
        row["name"]
        for row in conn.execute(
            "PRAGMA table_info(survey_responses)"
        ).fetchall()
    }

    # Add missing columns without deleting existing data.
    if "respondent_name" not in existing_columns:
        conn.execute(
            "ALTER TABLE survey_responses "
            "ADD COLUMN respondent_name TEXT"
        )

    if "respondent_age" not in existing_columns:
        conn.execute(
            "ALTER TABLE survey_responses "
            "ADD COLUMN respondent_age INTEGER"
        )

    for i in range(1, 21):
        column_name = f"q{i}"

        if column_name not in existing_columns:
            conn.execute(
                f"ALTER TABLE survey_responses "
                f"ADD COLUMN {column_name} TEXT"
            )

    conn.commit()
    conn.close()


# =====================================
# HOME PAGE
# =====================================

@app.route("/")
def home():
    return render_template("index.html")


# =====================================
# SURVEY PAGE
# =====================================

@app.route("/survey")
def survey():
    return render_template("survey.html")


# =====================================
# SUBMIT SURVEY
# =====================================

@app.route("/submit-survey", methods=["POST"])
def submit_survey():
    name = request.form.get("respondent_name", "").strip()
    age_text = request.form.get("respondent_age", "").strip()

    if not name:
        return "Please enter your name.", 400

    try:
        age = int(age_text)
    except (ValueError, TypeError):
        return "Please enter a valid age.", 400

    if not 1 <= age <= 120:
        return "Age must be between 1 and 120.", 400

    answers = []

    for i in range(1, 21):
        answer = request.form.get(f"q{i}", "").strip()

        if answer not in ("Yes", "No"):
            return f"Please answer question {i}.", 400

        answers.append(answer)

    columns = [
        "respondent_name",
        "respondent_age"
    ] + [f"q{i}" for i in range(1, 21)]

    placeholders = ", ".join(["?"] * len(columns))
    column_sql = ", ".join(columns)

    values = [name, age] + answers

    conn = get_db_connection()

    conn.execute(
        f"""
        INSERT INTO survey_responses ({column_sql})
        VALUES ({placeholders})
        """,
        values
    )

    conn.commit()
    conn.close()

    return redirect(url_for("thank_you"))


# =====================================
# THANK YOU PAGE
# =====================================

@app.route("/thank-you")
def thank_you():
    return render_template("thank_you.html")


# =====================================
# ADMIN LOGIN
# =====================================

@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():
    if session.get("admin_logged_in"):
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        password = request.form.get("password", "")

        if password == ADMIN_PASSWORD:
            session.clear()
            session["admin_logged_in"] = True
            return redirect(url_for("dashboard"))

        return render_template(
            "admin_login.html",
            error="Incorrect password. Please try again."
        )

    return render_template("admin_login.html")


# =====================================
# ADMIN LOGOUT
# =====================================

@app.route("/admin-logout", methods=["GET", "POST"])
def admin_logout():
    session.clear()
    return redirect(url_for("admin_login"))


# =====================================
# ADMIN ACCESS CHECK
# =====================================

def admin_required():
    return bool(session.get("admin_logged_in"))


# =====================================
# DASHBOARD / RESULTS DATA
# =====================================

def get_survey_data():
    conn = get_db_connection()

    responses = conn.execute(
        "SELECT * FROM survey_responses ORDER BY id DESC"
    ).fetchall()

    conn.close()

    total = len(responses)
    question_yes = {}

    for i in range(1, 21):
        question_yes[f"q{i}"] = sum(
            1 for response in responses
            if response[f"q{i}"] == "Yes"
        )

    def percentage(count):
        if total == 0:
            return 0
        return round(count * 100 / total)

    return {
        "responses": responses,
        "total": total,
        "question_yes": question_yes,
        "climate_yes": question_yes["q1"],
        "local_yes": question_yes["q2"],
        "waste_yes": question_yes["q6"],
        "rainwater_yes": question_yes["q8"],
        "climate_percent": percentage(question_yes["q1"]),
        "local_percent": percentage(question_yes["q2"]),
        "waste_percent": percentage(question_yes["q6"]),
        "rainwater_percent": percentage(question_yes["q8"]),
    }


# =====================================
# RESULTS PAGE - ADMIN ONLY
# =====================================

@app.route("/results")
def results():
    if not admin_required():
        return redirect(url_for("admin_login"))

    data = get_survey_data()

    live_data = {
        **data,
        "question_yes": data["question_yes"]
    }

    return render_template(
        "results.html",
        responses=data["responses"],
        live_data=live_data
    )


# =====================================
# DASHBOARD PAGE - ADMIN ONLY
# =====================================

@app.route("/dashboard")
def dashboard():
    if not admin_required():
        return redirect(url_for("admin_login"))

    data = get_survey_data()

    return render_template(
        "dashboard.html",
        dashboard_data=data
    )


# =====================================
# INITIALIZE DATABASE
# =====================================

init_db()


# =====================================
# START APPLICATION
# =====================================

if __name__ == "__main__":
    app.run(
        debug=True,
        host="127.0.0.1",
        port=5000
    )