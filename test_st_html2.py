import streamlit as st

st.title("Test st.html with script")

# Test with simple script
st.html('<script>console.log("test script"); window.testScript = "executed";</script>', unsafe_allow_javascript=True)
st.write('After simple script')

# Test with our landmark fix script
from components.ui.accessibility import render_landmark_fix_script
st.html(render_landmark_fix_script(), unsafe_allow_javascript=True)
st.write('After landmark fix script')

# Test with skip link
from components.ui.accessibility import render_skip_link
st.markdown(render_skip_link("main-content"), unsafe_allow_html=True)
st.write('After skip link')