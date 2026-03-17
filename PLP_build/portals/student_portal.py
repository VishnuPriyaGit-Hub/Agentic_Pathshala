import streamlit as st
from auth import add_student, login_student, hash_password, reset_student_password

def student_portal():

    st.subheader("Student Portal")

    tab1,tab2,tab3 = st.tabs(["Login","Sign Up","Reset Password"])


    # LOGIN
    with tab1:

        username = st.text_input("Username",key="stu_login_user")

        password = st.text_input("Password",type="password")

        if st.button("Login Student"):

            hashed = hash_password(password)

            user = login_student(username,hashed)

            if user:
                st.success("Login Successful")
            else:
                st.error("Invalid credentials")


    # SIGNUP
    with tab2:

        full_name = st.text_input("Enter Full Name")

        username = st.text_input("Create Username")

        password = st.text_input("Create Password",type="password")

        grade = st.selectbox("Grade",list(range(1,13)))

        roll = st.number_input("Roll Number",min_value=1)

        if st.button("Register Student"):

            hashed = hash_password(password)

            add_student(full_name,username,hashed,grade,roll)

            st.success("Student Registered")


    # RESET PASSWORD
    with tab3:

        username = st.text_input("Username")

        new_password = st.text_input("New Password",type="password")

        if st.button("Reset Student Password"):

            hashed = hash_password(new_password)

            reset_student_password(username,hashed)

            st.success("Password Updated")