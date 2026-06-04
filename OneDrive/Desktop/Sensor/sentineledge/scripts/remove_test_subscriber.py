import sqlite3, os, sys

db = os.path.join(os.path.dirname(__file__), '..', 'database', 'sentineledge.db')
db = os.path.normpath(db)
conn = sqlite3.connect(db)
cur = conn.execute("SELECT id, name, email FROM subscribers WHERE email='test@test.com'")
rows = cur.fetchall()
if rows:
    conn.execute("DELETE FROM subscribers WHERE email='test@test.com'")
    conn.commit()
    print(f'Removed {len(rows)} test subscriber(s): {rows}')
else:
    print('No test@test.com subscriber found (already clean)')
conn.close()
