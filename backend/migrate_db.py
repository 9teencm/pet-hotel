"""
一次性資料庫遷移腳本。
在 backend/ 目錄下執行：python migrate_db.py
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "instance", "pet_system.db")


def col_exists(cursor, table, column):
    cursor.execute(f"PRAGMA table_info({table})")
    return any(row[1] == column for row in cursor.fetchall())


def add_col(cursor, table, column, definition):
    if not col_exists(cursor, table, column):
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
        print(f"  + {table}.{column}")
    else:
        print(f"  = {table}.{column} (already exists)")


def main():
    print(f"DB: {DB_PATH}")
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    print("\n[pets]")
    add_col(cur, "pets", "breed",                  "VARCHAR(80)")
    add_col(cur, "pets", "chip_id",                "VARCHAR(30)")
    # UNIQUE index for chip_id (SQLite doesn't support ADD COLUMN ... UNIQUE)
    cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_pets_chip_id ON pets(chip_id)")
    add_col(cur, "pets", "rabies_vaccine_expiry",  "DATE")
    add_col(cur, "pets", "combo_vaccine_expiry",   "DATE")
    add_col(cur, "pets", "behavior_tag",           "VARCHAR(20)")
    add_col(cur, "pets", "dietary_notes",          "TEXT")

    print("\n[bookings]")
    add_col(cur, "bookings", "room_id",  "INTEGER REFERENCES rooms(id)")
    add_col(cur, "bookings", "roomCode", "VARCHAR(20)")

    print("\n建立新資料表（若不存在）...")
    # rooms
    cur.execute("""
        CREATE TABLE IF NOT EXISTS rooms (
            id         INTEGER PRIMARY KEY,
            room_code  VARCHAR(20) UNIQUE NOT NULL,
            room_type  VARCHAR(30) NOT NULL,
            status     VARCHAR(20) NOT NULL DEFAULT 'available',
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("  = rooms")

    # grooming_services
    cur.execute("""
        CREATE TABLE IF NOT EXISTS grooming_services (
            id               INTEGER PRIMARY KEY,
            pet_id           INTEGER NOT NULL REFERENCES pets(id),
            groomer_id       INTEGER REFERENCES users(id),
            service_type     VARCHAR(20) NOT NULL DEFAULT 'bath',
            status           VARCHAR(20) NOT NULL DEFAULT 'waiting',
            appointment_date DATE NOT NULL,
            notes            TEXT,
            photo_url        TEXT,
            photo_message    VARCHAR(500),
            photo_uploaded_at DATETIME,
            owner_notified   BOOLEAN NOT NULL DEFAULT 0,
            created_at       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("  = grooming_services")

    con.commit()
    con.close()
    print("\n完成！")


if __name__ == "__main__":
    main()
