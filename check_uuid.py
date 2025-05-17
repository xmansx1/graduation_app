import sqlite3

uuid_to_check = 'e23f9618-bd55-4c08-9322-3189b2a1eefb'  # ضع هنا UUID الذي جربته

conn = sqlite3.connect("invitations.db")
cur = conn.cursor()

cur.execute("SELECT name, national_id, used FROM invitations WHERE id = ?", (uuid_to_check,))
row = cur.fetchone()

if row:
    print("✅ الدعوة موجودة")
    print(f"الاسم: {row[0]}")
    print(f"الهوية: {row[1]}")
    print(f"الحالة: {'مستخدمة' if row[2] else 'صالحة'}")
else:
    print("❌ هذه الدعوة غير موجودة في قاعدة البيانات")
