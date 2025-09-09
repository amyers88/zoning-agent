import streamlit as st

st.set_page_config(
    page_title="Test Streamlit",
    page_icon="✅",
    layout="wide"
)

st.title("✅ Streamlit Test Page")
st.write("If you can see this, Streamlit is working correctly!")

with st.sidebar:
    st.header("Test Controls")
    if st.button("Click me!"):
        st.balloons()

st.write("## System Information")
st.json({
    "streamlit_version": st.__version__,
    "python_version": "3.12.0",
    "operating_system": "macOS"
})
