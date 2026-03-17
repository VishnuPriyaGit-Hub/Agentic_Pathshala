import streamlit as st
from auth import (
    login_teacher,
    add_teacher,
    reset_teacher_password,
    hash_password
)

from pages.approve_parent import approve_parent
from pages.generate_material import generate_material
from pages.dashboard import class_dashboard
from pages.generate_assessment import generate_assessment

def teacher_portal():

    # ---------------------------
    # Session state initialization
    # ---------------------------

    if "teacher_logged" not in st.session_state:
        st.session_state.teacher_logged = False

    if "teacher_name" not in st.session_state:
        st.session_state.teacher_name = None


    # ---------------------------
    # LOGIN / SIGNUP / RESET UI
    # ---------------------------

    if not st.session_state.teacher_logged:

        st.subheader("Teacher Portal")

        tab1, tab2, tab3 = st.tabs(
            ["Login", "Sign Up", "Reset Password"]
        )


        # ---------------------------
        # LOGIN TAB
        # ---------------------------

        with tab1:

            username = st.text_input(
                "Username",
                key="teacher_login_user"
            )

            password = st.text_input(
                "Password",
                type="password",
                key="teacher_login_pass"
            )

            if st.button("Login Teacher"):

                hashed = hash_password(password)

                user = login_teacher(
                    username,
                    hashed
                )

                if user:

                    st.session_state.teacher_logged = True
                    st.session_state.teacher_name = user[1]

                    st.success("Login successful")

                    st.rerun()

                else:
                    st.error("Invalid credentials")


        # ---------------------------
        # SIGN UP TAB
        # ---------------------------

        with tab2:

            full_name = st.text_input(
                "Enter Full Name",
                key="teacher_signup_name"
            )

            username = st.text_input(
                "Create Username",
                key="teacher_signup_user"
            )

            password = st.text_input(
                "Create Password",
                type="password",
                key="teacher_signup_pass"
            )

            if st.button("Register Teacher"):

                hashed = hash_password(password)

                add_teacher(
                    full_name,
                    username,
                    hashed
                )

                st.success("Teacher Registered Successfully")


        # ---------------------------
        # RESET PASSWORD TAB
        # ---------------------------

        with tab3:

            username = st.text_input(
                "Username",
                key="teacher_reset_user"
            )

            new_password = st.text_input(
                "New Password",
                type="password",
                key="teacher_reset_pass"
            )

            if st.button("Reset Teacher Password"):

                hashed = hash_password(new_password)

                reset_teacher_password(
                    username,
                    hashed
                )

                st.success("Password Updated Successfully")


    # ---------------------------
    # TEACHER DASHBOARD
    # ---------------------------

    else:

        st.sidebar.title("Teacher Navigation")

        menu = st.sidebar.radio(
            "Select Option",
            [
                "Map Students Grade",
                "Approve Parents Access",
                "Generate Learning Material",
                "Generate Assessment",
                "Class Performance Dashboard"
            ]
        )


        # Top right welcome message
        col1, col2 = st.columns([6,2])

        with col2:
            st.write(
                f"Welcome {st.session_state.teacher_name}!"
            )


        # ---------------------------
        # MENU OPTIONS
        # ---------------------------

        if menu == "Approve Parents Access":

            approve_parent()


        elif menu == "Generate Learning Material":

            generate_material()


        elif menu == "Class Performance Dashboard":

            class_dashboard()


        elif menu == "Map Students Grade":

            st.subheader("Map Students Grade")

            st.info(
                "Feature can be implemented to assign grades to students."
            )


        elif menu == "Generate Assessment":

            # st.subheader("Generate Assessment")

            # st.info(
            #     "Feature to allow teachers to create assessments."
            # )
            generate_assessment()


        # ---------------------------
        # LOGOUT BUTTON
        # ---------------------------

        st.sidebar.markdown("---")

        if st.sidebar.button("Logout"):

            st.session_state.teacher_logged = False
            st.session_state.teacher_name = None

            st.rerun()