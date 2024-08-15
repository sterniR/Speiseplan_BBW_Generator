import sqlite3

def create_database():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS meals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        day TEXT NOT NULL,
        date TEXT NOT NULL,
        meal1 TEXT NOT NULL,
        meal2 TEXT NOT NULL,
        salad TEXT NOT NULL,
        dessert TEXT NOT NULL
    )
    ''')

    conn.commit()
    conn.close()

if __name__ == "__main__":
    create_database()
    print("Datenbank und Tabelle erfolgreich erstellt.")
