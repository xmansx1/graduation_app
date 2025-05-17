from flask import Flask, request, render_template
import sqlite3

app = Flask(__name__)
db_path = "invitations.db"

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
            cur.execute("UPDATE invitations SET used = 1 WHERE id = ?", (invitation_id,))
            conn.commit()
            row = (row[0], row[1], 1)

        conn.close()

        if row:
            name, national_id, used = row

    return render_template("index.html", name=name, national_id=national_id, used=used, invitation_id=invitation_id)

if __name__ == "__main__":
    print("✅ التطبيق يعمل الآن على http://127.0.0.1:5000")
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

    from flask import jsonify

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
