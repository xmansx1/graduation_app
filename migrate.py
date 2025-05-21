import sqlite3

conn = sqlite3.connect("invitations.db")
cur = conn.cursor()

# تحقق إن كان العمود موجوداً قبل إضافته
try:
    cur.execute("ALTER TABLE invitations ADD COLUMN last_check TEXT")
    print("✅ تم إضافة العمود 'last_check' بنجاح.")
except sqlite3.OperationalError as e:
    print("⚠️", e)

conn.commit()
conn.close()
