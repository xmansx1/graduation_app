from flask import Flask, request, render_template, jsonify, redirect, send_file, session, url_for
import sqlite3
import os
import csv
import uuid
from io import BytesIO, StringIO
from functools import wraps
from flask import flash

app = Flask(__name__)
app.secret_key = 'secure-secret-key'
db_path = "invitations.db"

# ---------------------- AUTH ---------------------- #
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        if request.form['username'] == "admin" and request.form['password'] == "admin123":
            session['logged_in'] = True
            return redirect("/dashboard")
        else:
            error = "اسم المستخدم أو كلمة المرور غير صحيحة"
    return render_template("login.html", error=error)

@app.route("/logout")
def logout():
    session.pop('logged_in', None)
    return redirect("/login")

# ---------------------- VERIFY ---------------------- #
@app.route("/", methods=["GET", "POST"])
def verify():
    invitation_id = request.args.get("id", "") if request.method == "GET" else request.form.get("id", "")
    name, national_id, used = None, None, None

    if invitation_id:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("SELECT name, national_id, used FROM invitations WHERE id = ?", (invitation_id,))
        row = cur.fetchone()

        if request.method == "POST" and row and not row[2]:
            cur.execute("UPDATE invitations SET used = 1, last_check=CURRENT_TIMESTAMP WHERE id = ?", (invitation_id,))
            conn.commit()
            row = (row[0], row[1], 1)

        conn.close()

        if row:
            name, national_id, used = row

    return render_template("index.html", name=name, national_id=national_id, used=used, invitation_id=invitation_id)

@app.route("/reset", methods=["POST"])
@login_required
def reset_invitation():
    invitation_id = request.form.get("id")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("UPDATE invitations SET used = 0 WHERE id = ?", (invitation_id,))
    conn.commit()
    conn.close()
    return redirect("/dashboard")

# ---------------------- DASHBOARD ---------------------- #
@app.route("/dashboard")
@login_required
def dashboard():
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT name, national_id, used, id, last_check FROM invitations")
    invitations = cur.fetchall()

    cur.execute("SELECT COUNT(*) FROM invitations")
    total = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM invitations WHERE used = 1")
    used = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM invitations WHERE used = 0")
    valid = cur.fetchone()[0]

    conn.close()
    return render_template("dashboard.html", invitations=invitations, total=total, used=used, valid=valid)

# ---------------------- EXPORT CSV ---------------------- #
@app.route("/export")
@login_required
def export_csv():
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT name, national_id, id, used FROM invitations")
    rows = cur.fetchall()
    conn.close()

    si = StringIO()
    writer = csv.writer(si)
    writer.writerow(["الاسم", "الهوية", "UUID", "الحالة"])
    for row in rows:
        writer.writerow(row)

    output = BytesIO()
    output.write(si.getvalue().encode('utf-8'))
    output.seek(0)

    return send_file(
        output,
        mimetype='text/csv',
        as_attachment=True,
        download_name='invitations_export.csv'
    )

# ---------------------- API ---------------------- #
@app.route("/api/verify")
def api_verify():
    invitation_id = request.args.get("id", "")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT name, national_id, used FROM invitations WHERE id = ?", (invitation_id,))
    row = cur.fetchone()
    conn.close()

    if row:
        return jsonify({"name": row[0], "national_id": row[1], "used": bool(row[2])})
    else:
        return jsonify({})

# ---------------------- PRINT CARD ---------------------- #
@app.route("/print/<invitation_id>")
@login_required
def print_card(invitation_id):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT name, national_id FROM invitations WHERE id = ?", (invitation_id,))
    row = cur.fetchone()
    conn.close()
    if row:
        return render_template("print_card.html", name=row[0], national_id=row[1], qr_link=f"https://graduation-app.onrender.com/?id={invitation_id}")
    else:
        return "غير موجود", 404

# ---------------------- ADD STUDENT ---------------------- #
@app.route("/add", methods=["GET", "POST"])
@login_required
def add_student():
    if request.method == "POST":
        name = request.form.get("name")
        national_id = request.form.get("national_id")
        invitation_id = str(uuid.uuid4())
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("INSERT INTO invitations (id, name, national_id, used) VALUES (?, ?, ?, 0)",
                    (invitation_id, name, national_id))
        conn.commit()
        conn.close()
        flash("✅ تم إضافة الطالب بنجاح", "success")

        return redirect("/dashboard")
    return render_template("add_student.html")

# ---------------------- DELETE INVITATION ---------------------- #
@app.route("/delete/<invitation_id>", methods=["POST"])
@login_required
def delete_invitation(invitation_id):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("DELETE FROM invitations WHERE id = ?", (invitation_id,))
    conn.commit()
    conn.close()
    flash("🗑️ تم حذف الدعوة بنجاح", "danger")

    return redirect("/dashboard")

# ---------------------- MAIN ---------------------- #
if __name__ == "__main__":
    print("✅ التطبيق يعمل الآن على http://127.0.0.1:5000")
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
