import streamlit as st
from auth import add_parent, login_parent, hash_password, reset_parent_password

def parent_portal():

    st.subheader("Parent Portal")

    tab1,tab2,tab3 = st.tabs(["Login","Sign Up","Reset Password"])


    # LOGIN
    with tab1:

        username = st.text_input("Username",key="parent_login_user")

        password = st.text_input("Password",type="password")

        if st.button("Login Parent"):

            hashed = hash_password(password)

            user = login_parent(username,hashed)

            if user:
                st.success("Login Successful")
            else:
                st.error("Invalid credentials")


    # SIGNUP
    with tab2:

        full_name = st.text_input("Enter Full Name")

        username = st.text_input("Create Username")

        password = st.text_input("Create Password",type="password")

        email = st.text_input("Enter Mail ID")

        if st.button("Register Parent"):

            hashed = hash_password(password)

            add_parent(full_name,username,hashed,email)

            st.success("Parent Registered")


    # RESET PASSWORD
    with tab3:

        username = st.text_input("Username")

        new_password = st.text_input("New Password",type="password")

        if st.button("Reset Parent Password"):

            hashed = hash_password(new_password)

            reset_parent_password(username,hashed)

            st.success("Password Updated")