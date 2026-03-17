import hashlib
from database import conn, cursor


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


# ------------------------
# STUDENT
# ------------------------

def add_student(full_name, username, password, grade, roll):

    cursor.execute("""
    INSERT INTO students(full_name,username,password,grade,roll_number)
    VALUES(?,?,?,?,?)
    """,(full_name,username,password,grade,roll))

    conn.commit()


def login_student(username,password):

    cursor.execute(
    "SELECT * FROM students WHERE username=? AND password=?",
    (username,password))

    return cursor.fetchone()


# ------------------------
# PARENT
# ------------------------

def add_parent(full_name,username,password,email):

    cursor.execute("""
    INSERT INTO parents(full_name,username,password,email)
    VALUES(?,?,?,?)
    """,(full_name,username,password,email))

    conn.commit()


def login_parent(username,password):

    cursor.execute(
    "SELECT * FROM parents WHERE username=? AND password=?",
    (username,password))

    return cursor.fetchone()


# ------------------------
# TEACHER
# ------------------------

def add_teacher(full_name,username,password):

    cursor.execute("""
    INSERT INTO teachers(full_name,username,password)
    VALUES(?,?,?)
    """,(full_name,username,password))

    conn.commit()


def login_teacher(username,password):

    cursor.execute(
    "SELECT * FROM teachers WHERE username=? AND password=?",
    (username,password))

    return cursor.fetchone()

# ------------------------
# RESET PASSWORD
# ------------------------

def reset_student_password(username, new_password):

    cursor.execute(
    """
    UPDATE students
    SET password=?
    WHERE username=?
    """,
    (new_password, username)
    )

    conn.commit()


def reset_parent_password(username, new_password):

    cursor.execute(
    """
    UPDATE parents
    SET password=?
    WHERE username=?
    """,
    (new_password, username)
    )

    conn.commit()


def reset_teacher_password(username, new_password):

    cursor.execute(
    """
    UPDATE teachers
    SET password=?
    WHERE username=?
    """,
    (new_password, username)
    )

    conn.commit()