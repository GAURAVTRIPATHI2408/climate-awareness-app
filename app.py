from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import os

app = Flask(__name__)

DATABASE = "database.db"


# ==============================
# SECRET KEY & ADMIN PASSWORD
# ==============================

# Vercel par Environment Variables se values li jayengi.
# Local testing ke liye default values rakhi gayi hain.

app.secret_key = os.environ.get(
    "SECRET_KEY",
    "climate-awareness-secret-key-change-this"
)

ADMIN_PASSWORD = os.environ.get(
    "ADMIN_PASSWORD",
    "admin123"
)


# ==============================
# SESSION SECURITY
# ==============================

app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"


# ==============================
# DATABASE CONNECTION
# ==============================

def get_db_connection():

    conn = sqlite3.connect(DATABASE)

    conn.row_factory = sqlite3.Row

    return conn


# ==============================
# CREATE / UPDATE DATABASE TABLE
# ==============================

def init_db():

    conn = get_db_connection()

    # Original columns are kept
    # so existing data is not lost

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
            tree_drive TEXT

        )
    """)

    conn.commit()


    # Add q1-q20 columns
    # if they do not already exist

    existing_columns = conn.execute(
        "PRAGMA table_info(survey_responses)"
    ).fetchall()

    existing_names = {
        column["name"]
        for column in existing_columns
    }


    for i in range(1, 21):

        column_name = f"q{i}"

        if column_name not in existing_names:

            conn.execute(
                f"""
                ALTER TABLE survey_responses
                ADD COLUMN {column_name} TEXT
                """
            )


    conn.commit()

    conn.close()


# ==============================
# HOME PAGE
# ==============================

@app.route("/")
def home():

    return render_template("index.html")


# ==============================
# SURVEY PAGE
# ==============================

@app.route("/survey")
def survey():

    return render_template("survey.html")


# ==============================
# SUBMIT SURVEY
# ==============================

@app.route("/submit-survey", methods=["POST"])
def submit_survey():

    # Get all 20 answers

    answers = []

    for i in range(1, 21):

        answer = request.form.get(f"q{i}")

        answers.append(answer)


    conn = get_db_connection()


    # Insert all 20 answers

    conn.execute("""
        INSERT INTO survey_responses
        (
            q1,
            q2,
            q3,
            q4,
            q5,
            q6,
            q7,
            q8,
            q9,
            q10,
            q11,
            q12,
            q13,
            q14,
            q15,
            q16,
            q17,
            q18,
            q19,
            q20
        )
        VALUES (
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
        )
    """, answers)


    conn.commit()

    conn.close()


    # IMPORTANT:
    # Survey submit karne ke baad
    # results nahi dikhayenge.
    # Sirf Thank You page khulega.

    return redirect(url_for("thank_you"))


# ==============================
# THANK YOU PAGE
# ==============================

@app.route("/thank-you")
def thank_you():

    return render_template("thank_you.html")


# ==============================
# ADMIN LOGIN
# ==============================

@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():

    # Already logged in hai to dashboard bhejo

    if session.get("admin_logged_in"):

        return redirect(url_for("dashboard"))


    if request.method == "POST":

        password = request.form.get("password", "")


        if password == ADMIN_PASSWORD:

            session["admin_logged_in"] = True

            return redirect(url_for("dashboard"))


        return render_template(
            "admin_login.html",
            error="Incorrect password. Please try again."
        )


    return render_template("admin_login.html")


# ==============================
# ADMIN LOGOUT
# ==============================

@app.route("/admin-logout")
def admin_logout():

    session.pop("admin_logged_in", None)

    return redirect(url_for("admin_login"))


# ==============================
# ADMIN CHECK
# ==============================

def admin_required():

    if not session.get("admin_logged_in"):

        return False

    return True


# ==============================
# RESULTS PAGE
# ==============================

@app.route("/results")
def results():

    # Public users cannot access results

    if not admin_required():

        return redirect(url_for("admin_login"))


    conn = get_db_connection()


    responses = conn.execute(
        "SELECT * FROM survey_responses"
    ).fetchall()


    total = len(responses)


    # Percentage function

    def percentage(count):

        if total == 0:

            return 0

        return round((count / total) * 100)


    # ==============================
    # QUESTION-WISE YES COUNTS
    # ==============================

    question_yes = {}


    for i in range(1, 21):

        question_yes[f"q{i}"] = sum(

            1
            for r in responses
            if r[f"q{i}"] == "Yes"

        )


    # ==============================
    # MAIN CLIMATE INDICATORS
    # ==============================

    climate_yes = question_yes["q1"]

    local_yes = question_yes["q2"]

    waste_yes = question_yes["q6"]

    rainwater_yes = question_yes["q8"]


    conn.close()


    # ==============================
    # LIVE DATA
    # ==============================

    live_data = {

        "total": total,

        "climate_yes": climate_yes,

        "climate_percent":
            percentage(climate_yes),


        "local_yes": local_yes,

        "local_percent":
            percentage(local_yes),


        "waste_yes": waste_yes,

        "waste_percent":
            percentage(waste_yes),


        "rainwater_yes": rainwater_yes,

        "rainwater_percent":
            percentage(rainwater_yes),


        "question_yes":
            question_yes

    }


    return render_template(
        "results.html",
        responses=responses,
        live_data=live_data
    )


# ==============================
# DASHBOARD PAGE
# ==============================

@app.route("/dashboard")
def dashboard():

    # IMPORTANT:
    # Dashboard sirf admin login ke baad khulega.

    if not admin_required():

        return redirect(url_for("admin_login"))


    conn = get_db_connection()


    responses = conn.execute(
        "SELECT * FROM survey_responses"
    ).fetchall()


    total = len(responses)


    # Percentage function

    def percentage(count):

        if total == 0:

            return 0

        return round((count / total) * 100)


    # ==============================
    # QUESTION-WISE YES COUNTS
    # ==============================

    question_yes = {}


    for i in range(1, 21):

        question_yes[f"q{i}"] = sum(

            1
            for r in responses
            if r[f"q{i}"] == "Yes"

        )


    # ==============================
    # MAIN DASHBOARD INDICATORS
    # ==============================

    climate_yes = question_yes["q1"]

    local_yes = question_yes["q2"]

    waste_yes = question_yes["q6"]

    rainwater_yes = question_yes["q8"]


    conn.close()


    # ==============================
    # DASHBOARD DATA
    # ==============================

    dashboard_data = {

        "total": total,

        "climate_percent":
            percentage(climate_yes),

        "local_percent":
            percentage(local_yes),

        "waste_percent":
            percentage(waste_yes),

        "rainwater_percent":
            percentage(rainwater_yes),

        "question_yes":
            question_yes

    }


    return render_template(
        "dashboard.html",
        dashboard_data=dashboard_data
    )


# ==============================
# INITIALIZE DATABASE
# ==============================

# App start hote hi database initialize hoga.
# Local aur deployment dono ke liye useful.

init_db()


# ==============================
# START APPLICATION
# ==============================

if __name__ == "__main__":

    app.run(
        debug=True,
        host="127.0.0.1",
        port=5000
    )