import sqlite3

def upgrade():
    conn = sqlite3.connect(r'd:\QR\instance\university.db')
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE faculty ADD COLUMN photo_url VARCHAR(255)")
        print("Column added successfully.")
    except sqlite3.OperationalError as e:
        print("Error/Already exists:", e)
    conn.commit()
    conn.close()

if __name__ == "__main__":
    upgrade()
