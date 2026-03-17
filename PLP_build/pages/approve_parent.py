import streamlit as st
import sqlite3


def approve_parent():

    conn = sqlite3.connect("school.db")
    cursor = conn.cursor()

    students = cursor.execute(
    "SELECT id,full_name FROM students").fetchall()

    parents = cursor.execute(
    "SELECT id,full_name,email FROM parents").fetchall()

    student_dict={s[1]:s[0] for s in students}
    parent_dict={p[1]:p[0] for p in parents}
    parent_email={p[1]:p[2] for p in parents}

    student = st.selectbox(
    "Select Student",
    list(student_dict.keys()))

    parent = st.selectbox(
    "Select Parent",
    list(parent_dict.keys()))

    st.text_input(
    "Parent Email",
    value=parent_email[parent],
    disabled=True)

    if st.button("Provide Access"):

        cursor.execute("""
        INSERT INTO parent_student_map(parent_id,student_id)
        VALUES(?,?)
        """,(parent_dict[parent],student_dict[student]))

        conn.commit()

        st.success("Access granted")