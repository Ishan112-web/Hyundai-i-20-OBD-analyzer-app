import streamlit as st

st.title("Test Minimal Script")

# Test minimal landmark fix script
minimal_script = """
<script>
(function() {
    function fixLandmarks() {
        console.log('fixLandmarks called');
        const mainContent = document.getElementById('stMain');
        if (mainContent) {
            mainContent.setAttribute('id', 'main-content');
            console.log('Set main-content id');
        }
    }
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', fixLandmarks);
    } else {
        fixLandmarks();
    }
    window.i20FixLandmarks = fixLandmarks;
})();
</script>
"""

st.html(minimal_script, unsafe_allow_javascript=True)
st.write('After minimal script')

# Test with MutationObserver
script_with_observer = """
<script>
const observer = new MutationObserver(() => {
    console.log('Mutation observed');
});
observer.observe(document.body, { childList: true, subtree: true });
console.log('Observer created');
</script>
"""

st.html(script_with_observer, unsafe_allow_javascript=True)
st.write('After observer script')

# Test with innerHTML
script_with_innerhtml = """
<script>
const div = document.createElement('div');
div.innerHTML = '<span>test</span>';
document.body.appendChild(div);
console.log('innerHTML test');
</script>
"""

st.html(script_with_innerhtml, unsafe_allow_javascript=True)
st.write('After innerHTML script')