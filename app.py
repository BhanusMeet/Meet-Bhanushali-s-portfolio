from __future__ import annotations

import os
import sqlite3
from functools import wraps
from typing import Any

from flask import (
    Flask,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-me")
app.config["DATABASE"] = os.path.join(app.root_path, "portfolio.db")


PROJECTS = [
    {
        "name": "E-commerce Operations Engine — Vintage Recipes",
        "status": "Completed",
        "description": "Managed end-to-end backend operations for a growing D2C brand, optimized the Shopify store for better conversions, managed Amazon listings, and engineered WhatsApp automation.",
        "impact": "Reduced manual query handling time by 40% through automation.",
        "link": "https://www.vintagerecipes.in",
    },
    {
        "name": "Digital Growth Transformation — M. Motilal Masalawala",
        "status": "Completed",
        "description": "Handled Shopify development and executed performance marketing via Google & Meta Ads for a 112-year-old family business.",
        "impact": "Bridged legacy business operations with modern digital scalability.",
        "link": "https://motilalmasala.com",
    },
]

CERTIFICATIONS = [
    {
        "title": "Ethical Hacking",
        "issuer": "Boston Institute of Analytics",
        "doc": "https://meetbhanushaliportfolio.netlify.app/certification",
    },
    {
        "title": "CyberSecurity",
        "issuer": "Boston Institute of Analytics",
        "doc": "https://meetbhanushaliportfolio.netlify.app/certification",
    },
    {
        "title": "Google Ads",
        "issuer": "Udemy",
        "doc": "https://meetbhanushaliportfolio.netlify.app/certification",
    },
]

SOCIALS = {
    "whatsapp": "https://wa.me/919876543210",
    "linkedin": "https://in.linkedin.com/in/meet-bhanushali-924b56369",
    "fiverr": "https://www.fiverr.com",
    "instagram": "https://www.instagram.com/meettbhanushali/",
    "tryhackme": "https://tryhackme.com/",
}


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        g.db = sqlite3.connect(app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exception: Exception | None) -> None:
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db() -> None:
    db = sqlite3.connect(app.config["DATABASE"])
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('admin','client'))
        );

        CREATE TABLE IF NOT EXISTS ratings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            stars INTEGER NOT NULL CHECK(stars BETWEEN 1 AND 5),
            comment TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id),
            FOREIGN KEY(user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS recommendations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending','approved','rejected')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        );
        """
    )

    admin_exists = db.execute("SELECT id FROM users WHERE role='admin' LIMIT 1").fetchone()
    if not admin_exists:
        db.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (?, ?, 'admin')",
            ("meet_admin", generate_password_hash("meet@secure")),
        )
    db.commit()
    db.close()


def login_required(role: str | None = None):
    def decorator(view):
        @wraps(view)
        def wrapped_view(*args: Any, **kwargs: Any):
            if "user_id" not in session:
                flash("Login required.", "error")
                return redirect(url_for("login"))
            if role and session.get("role") != role:
                flash("Unauthorized access.", "error")
                return redirect(url_for("index"))
            return view(*args, **kwargs)

        return wrapped_view

    return decorator


@app.route("/")
def index():
    db = get_db()
    ratings = db.execute(
        """
        SELECT r.stars, r.comment, u.username, r.created_at
        FROM ratings r JOIN users u ON r.user_id = u.id
        ORDER BY r.created_at DESC
        """
    ).fetchall()
    recommendations = db.execute(
        """
        SELECT rec.id, rec.content, rec.created_at, u.username
        FROM recommendations rec JOIN users u ON rec.user_id = u.id
        WHERE rec.status='approved'
        ORDER BY rec.created_at DESC
        """
    ).fetchall()

    avg_rating = db.execute("SELECT ROUND(AVG(stars),2) as avg_rating FROM ratings").fetchone()["avg_rating"]

    return render_template(
        "index.html",
        projects=PROJECTS,
        certifications=CERTIFICATIONS,
        socials=SOCIALS,
        ratings=ratings,
        recommendations=recommendations,
        avg_rating=avg_rating,
    )


@app.route("/certifications")
def certifications_page():
    return render_template("certifications.html", certifications=CERTIFICATIONS)


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]
        role = request.form.get("role", "client")

        if role != "client":
            flash("Public signup is only for clients.", "error")
            return redirect(url_for("signup"))

        db = get_db()
        try:
            db.execute(
                "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                (username, generate_password_hash(password), role),
            )
            db.commit()
            flash("Signup successful. Please login.", "success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("Username already exists.", "error")

    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]

        db = get_db()
        user = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()

        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["role"] = user["role"]
            flash("Welcome back.", "success")
            return redirect(url_for("admin" if user["role"] == "admin" else "index"))

        flash("Invalid credentials.", "error")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out.", "success")
    return redirect(url_for("index"))


@app.route("/rate", methods=["POST"])
@login_required(role="client")
def rate():
    stars = int(request.form["stars"])
    comment = request.form.get("comment", "").strip()

    db = get_db()
    db.execute(
        """
        INSERT INTO ratings (user_id, stars, comment)
        VALUES (?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET stars=excluded.stars, comment=excluded.comment, created_at=CURRENT_TIMESTAMP
        """,
        (session["user_id"], stars, comment),
    )
    db.commit()
    flash("Rating submitted.", "success")
    return redirect(url_for("index") + "#feedback")


@app.route("/recommend", methods=["POST"])
@login_required(role="client")
def recommend():
    content = request.form.get("content", "").strip()
    if len(content) < 8:
        flash("Recommendation must be at least 8 characters.", "error")
        return redirect(url_for("index") + "#feedback")

    db = get_db()
    db.execute(
        "INSERT INTO recommendations (user_id, content, status) VALUES (?, ?, 'pending')",
        (session["user_id"], content),
    )
    db.commit()
    flash("Recommendation submitted for review.", "success")
    return redirect(url_for("index") + "#feedback")


@app.route("/admin")
@login_required(role="admin")
def admin():
    db = get_db()
    ratings = db.execute(
        "SELECT r.id, r.stars, r.comment, r.created_at, u.username FROM ratings r JOIN users u ON r.user_id=u.id ORDER BY r.created_at DESC"
    ).fetchall()
    recommendations = db.execute(
        "SELECT rec.id, rec.content, rec.status, rec.created_at, u.username FROM recommendations rec JOIN users u ON rec.user_id=u.id ORDER BY rec.created_at DESC"
    ).fetchall()
    return render_template("admin.html", ratings=ratings, recommendations=recommendations)


@app.route("/admin/recommendation/<int:rec_id>/<action>", methods=["POST"])
@login_required(role="admin")
def moderate_recommendation(rec_id: int, action: str):
    if action not in {"approve", "reject", "delete"}:
        flash("Invalid action.", "error")
        return redirect(url_for("admin"))

    db = get_db()
    if action == "delete":
        db.execute("DELETE FROM recommendations WHERE id = ?", (rec_id,))
    else:
        db.execute("UPDATE recommendations SET status = ? WHERE id = ?", ("approved" if action == "approve" else "rejected", rec_id))
    db.commit()
    flash("Recommendation updated.", "success")
    return redirect(url_for("admin"))


@app.route("/admin/rating/<int:rating_id>/delete", methods=["POST"])
@login_required(role="admin")
def delete_rating(rating_id: int):
    db = get_db()
    db.execute("DELETE FROM ratings WHERE id = ?", (rating_id,))
    db.commit()
    flash("Rating deleted.", "success")
    return redirect(url_for("admin"))


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
