import streamlit as st


def generate_assessment():

    st.title("Generate Assessment")

    st.write("Provide the instruction for generating assessment content.")

    # Wide text field
    action_item = st.text_area(
        "Enter the action item",
        height=200,
        placeholder="Example: Generate Grade 5 Maths MCQ based assessment for roll number A123 on Fractions. Total questions to be 10 and complexity level should be easy."
    )

    st.write("")

    if st.button("Generate"):

        if action_item.strip() == "":
            st.warning("Please enter an action item.")

        else:
            st.success("Assessment generation request submitted.")

            st.write("### Action Item Submitted")
            st.write(action_item)