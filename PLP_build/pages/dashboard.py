import streamlit as st
import sqlite3


def class_dashboard():

    conn = sqlite3.connect("school.db")
    cursor = conn.cursor()

    students = cursor.execute(
    "SELECT full_name,grade,roll_number FROM students"
    ).fetchall()

    st.subheader("Class Performance Dashboard")

    for s in students:

        st.write(
        f"Student: {s[0]} | Grade: {s[1]} | Roll: {s[2]}"
        )