import sys
sys.path.insert(0, 'backend')
import os
os.environ.setdefault('APP_ENV', 'development')
from database.connection import execute_write, execute_read, init_db

init_db()

# Try inserting a reading
result = execute_write(
    "INSERT INTO readings (temperature, timestamp, is_valid) VALUES (?, ?, ?)",
    (38.5, "2026-06-03T09:30:00+00:00", 1)
)
print("Inserted row id:", result.lastrowid)

count = execute_read("SELECT COUNT(*) as c FROM readings")
print("Readings count after insert:", count[0]['c'])

# Clean up
execute_write("DELETE FROM readings WHERE temperature = 38.5")
count2 = execute_read("SELECT COUNT(*) as c FROM readings")
print("Readings count after cleanup:", count2[0]['c'])
