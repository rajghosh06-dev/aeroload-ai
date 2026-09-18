import streamlit as st

st.set_page_config(page_title="AeroLoad AI",
                   page_icon=" _:_ ",
                   layout="wide",
                   initial_sidebar_state="expanded"
                   )

st.title(" AeroLoad AI")
st.subheader("Aircraft Cargo Weight and Balance & Hazmat Placement Engine")
st.write(
    "An intelligent constraint-based aircraft cargo planning"
    "and safety analysis system."
)
st.success(
    "AeroLoad AI development environment is configured successfully"
)
st.caption("Project Status: Phase 0 - Foundation Setup")
