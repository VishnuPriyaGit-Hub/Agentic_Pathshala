import sqlite3


# ---------------------------------
# DATABASE CONNECTION
# ---------------------------------

def get_connection():
    conn = sqlite3.connect("school.db", check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


conn = get_connection()
cursor = conn.cursor()


# ---------------------------------
# STUDENTS TABLE
# ---------------------------------

cursor.execute("""
CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    grade INTEGER,
    roll_number INTEGER
)
""")


# ---------------------------------
# PARENTS TABLE
# ---------------------------------

cursor.execute("""
CREATE TABLE IF NOT EXISTS parents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    email TEXT
)
""")


# ---------------------------------
# TEACHERS TABLE
# ---------------------------------

cursor.execute("""
CREATE TABLE IF NOT EXISTS teachers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
)
""")


# ---------------------------------
# PARENT-STUDENT MAPPING
# ---------------------------------

cursor.execute("""
CREATE TABLE IF NOT EXISTS parent_student_map (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    parent_id INTEGER,
    student_id INTEGER,

    FOREIGN KEY (parent_id) REFERENCES parents(id) ON DELETE CASCADE,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,

    UNIQUE(parent_id, student_id)
)
""")


# ---------------------------------
# SAVE CHANGES
# ---------------------------------

conn.commit()