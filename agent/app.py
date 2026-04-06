import streamlit as st
from agent import run_agent
from PIL import Image

st.set_page_config(page_title="InsightFlow AI", layout="wide", page_icon="🤖")

st.title("🤖 AI Data Analyst Assistant - InsightFlow")
st.markdown("---")

# -------------------
# Sidebar Section
# -------------------
st.sidebar.header("💡 Suggestions")
examples = [
    "MRR growth by month",
    "Churn rate trend",
    "Active companies per month",
    "Avg MRR by industry",
    "Total events by event name"
]

selected_example = st.sidebar.selectbox("Choose a template:", [""] + examples)


st.sidebar.markdown("---")
st.sidebar.subheader("📌 Project Overview")
st.sidebar.info("""
This AI Agent analyzes a **simulated B2B SaaS ecosystem**. 
It translates natural language into complex SQL queries to extract 
insights from a BigQuery Data Warehouse modeled with dbt.
""")

st.sidebar.subheader("📫 Contact & Networking")
st.sidebar.write("If you'd like to discuss Data Engineering or AI, feel free to reach out!")

st.sidebar.markdown("[🔗 Connect on LinkedIn](www.linkedin.com/in/antuel-quirino)") 


user_input = st.text_input("Ask your data anything:", value=selected_example)

if st.button("🚀 Analyze"):
    if not user_input:
        st.warning("Please enter a question")
        st.stop()

    with st.spinner("Talking to BigQuery..."):
        result = run_agent(user_input)

    if "error" in result:
        st.error(f"Error: {result['error']}")
        if result.get("sql"):
            with st.expander("See attempted SQL"):
                st.code(result["sql"], language="sql")
    else:
        col1, col2 = st.columns([1, 1])

        with col1:
            st.subheader("📊 Data Result")
            st.dataframe(result["data"], use_container_width=True)
            
            with st.expander("🛠️ View Generated SQL"):
                st.code(result["sql"], language="sql")

        with col2:
            if result["chart"]:
                st.subheader("📈 Visualization")
                st.image(result["chart"])
            
            st.subheader("💡 AI Insights")
            st.write(result["insight"])