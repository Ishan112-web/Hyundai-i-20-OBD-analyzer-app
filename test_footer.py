import streamlit as st
from components.ui.accessibility import render_footer

st.title("Test Footer")

st.write("Before footer")
st.markdown(render_footer(), unsafe_allow_html=True)
st.write("After footer")