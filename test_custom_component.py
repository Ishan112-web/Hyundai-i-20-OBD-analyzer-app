import streamlit as st
from components.streamlit_components.document_html import document_html

st.title("Test Custom Component")

# Test the custom component
document_html('<div id="test-custom">Custom component test</div>', key="test1")
st.write('After custom component 1')

document_html('<script>console.log("Custom component script"); window.customComponentTest = "works";</script>', key="test2")
st.write('After custom component 2')

st.write('Done')