import streamlit as st


def generate_material():

    st.title("Generate Learning Material")

    st.write("Provide the instruction for generating learning content.")

    # Wide text field
    action_item = st.text_area(
        "Enter the action item",
        height=200,
        placeholder="Example: Generate Grade 5 Maths learning material on Fractions with 10 practice problems."
    )

    st.write("")

    if st.button("Generate"):

        if action_item.strip() == "":
            st.warning("Please enter an action item.")

        else:
            st.success("Learning material request submitted.")

            st.write("### Action Item Submitted")
            st.write(action_item)