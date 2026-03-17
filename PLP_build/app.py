import streamlit as st
from portals.student_portal import student_portal
from portals.parent_portal import parent_portal
from portals.teacher_portal import teacher_portal

# -----------------------------------
# PAGE CONFIG
# -----------------------------------

st.set_page_config(
    page_title="Pathshala - Personalized Learning Platform",
    layout="wide"
)

# -----------------------------------
# SESSION STATE INITIALIZATION
# -----------------------------------

if "portal" not in st.session_state:
    st.session_state.portal = None

if "teacher_logged" not in st.session_state:
    st.session_state.teacher_logged = False


# -----------------------------------
# HIDE DEFAULT SIDEBAR NAVIGATION
# -----------------------------------

st.markdown("""
<style>

/* Hide default Streamlit multipage navigation */
[data-testid="stSidebarNav"] {
display:none;
}

/* Hide sidebar initially */
[data-testid="stSidebar"] {
display:none;
}

/* Portal cards styling */

.portal-card {
background-color:white;
padding:40px;
border-radius:15px;
text-align:center;
box-shadow:0px 6px 15px rgba(0,0,0,0.1);
transition: transform 0.25s ease;
}

.portal-card:hover{
transform:scale(1.05);
}

.portal-icon{
font-size:60px;
}

.portal-title{
font-size:22px;
font-weight:600;
margin-top:10px;
}

</style>
""", unsafe_allow_html=True)


# -----------------------------------
# SHOW SIDEBAR ONLY FOR TEACHER LOGIN
# -----------------------------------

if st.session_state.teacher_logged:

    st.markdown("""
    <style>
    [data-testid="stSidebar"] {
    display:block;
    }
    </style>
    """, unsafe_allow_html=True)


# -----------------------------------
# HOME PAGE
# -----------------------------------

if st.session_state.portal is None:

    st.title("🎓 Pathshala - Personalized Learning Platform")

    st.write("")
    st.write("### Choose Your Portal")

    col1, col2, col3 = st.columns(3)

    # Parent Portal
    with col1:

        st.markdown("""
        <div class="portal-card">
        <div class="portal-icon">👨‍👩‍👧</div>
        <div class="portal-title">Parent Portal</div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("Enter Parent Portal", use_container_width=True):
            st.session_state.portal = "parent"
            st.rerun()

    # Teacher Portal
    with col2:

        st.markdown("""
        <div class="portal-card">
        <div class="portal-icon">👩‍🏫</div>
        <div class="portal-title">Teacher Portal</div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("Enter Teacher Portal", use_container_width=True):
            st.session_state.portal = "teacher"
            st.rerun()

    # Student Portal
    with col3:

        st.markdown("""
        <div class="portal-card">
        <div class="portal-icon">🎒</div>
        <div class="portal-title">Student Portal</div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("Enter Student Portal", use_container_width=True):
            st.session_state.portal = "student"
            st.rerun()


# -----------------------------------
# STUDENT PORTAL
# -----------------------------------

elif st.session_state.portal == "student":

    if st.button("⬅ Back to Home"):
        st.session_state.portal = None
        st.rerun()

    student_portal()


# -----------------------------------
# PARENT PORTAL
# -----------------------------------

elif st.session_state.portal == "parent":

    if st.button("⬅ Back to Home"):
        st.session_state.portal = None
        st.rerun()

    parent_portal()


# -----------------------------------
# TEACHER PORTAL
# -----------------------------------

elif st.session_state.portal == "teacher":

    if st.button("⬅ Back to Home"):
        st.session_state.portal = None
        st.session_state.teacher_logged = False
        st.rerun()

    teacher_portal()