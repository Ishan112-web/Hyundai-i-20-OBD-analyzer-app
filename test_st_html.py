import streamlit as st

st.title("Test st.html")

# Test st.html directly
st.html('<div id="test-div">Test content from st.html</div>')
st.write('After st.html')

# Test with script
st.html('<script>console.log("Script from st.html"); window.testVar = "hello";</script>', unsafe_allow_javascript=True)
st.write('After st.html with script')

# Test with skip link
st.html('<a href="#main-content" class="i20-skip-link" tabindex="0">Skip to main content</a>')
st.write('After skip link')