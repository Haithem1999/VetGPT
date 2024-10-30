import streamlit as st
import openai  # OpenAI API for LLM
import pandas as pd

# Streamlit page setup
st.set_page_config(page_title="Veterinarian Expert Chatbot", layout="wide")

# Set up OpenAI API (replace YOUR_API_KEY with your actual OpenAI API key)
openai.api_key = "YOUR_API_KEY"

# Initialize session state to store conversation and uploaded file data
if "messages" not in st.session_state:
    st.session_state["messages"] = []
if "file_data" not in st.session_state:
    st.session_state["file_data"] = None

st.title("Veterinarian Expert Chatbot")
st.write("Ask questions about animal symptoms, treatments, and more. You can also upload a medical file for analysis.")

# Define the function to generate a response using the LLM
def generate_response(question):
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=st.session_state["messages"] + [{"role": "user", "content": question}]
    )
    return response.choices[0].message.content

# Function to handle file analysis and summarize data
def summarize_data(file_data):
    # Summarize the data into key insights (customize this based on your needs)
    summary = "\n".join([f"{k}: {str(v)[:50]}..." for entry in file_data for k, v in entry.items()])
    return summary

def analyze_and_respond(question):
    if st.session_state["file_data"]:
        # Format file data into a readable format for the model
        file_summary = summarize_data(st.session_state["file_data"])
        prompt = f"File content: {file_summary}\nUser Question: {question}"
    else:
        prompt = question

    return generate_response(prompt)

# Handle file upload and display
uploaded_file = st.file_uploader("Upload a medical file (CSV, Excel, or JSON)", type=["csv", "xlsx", "json"])

if uploaded_file:
    if uploaded_file.name.endswith(".csv"):
        data = pd.read_csv(uploaded_file)
    elif uploaded_file.name.endswith(".xlsx"):
        data = pd.read_excel(uploaded_file)
    elif uploaded_file.name.endswith(".json"):
        data = pd.read_json(uploaded_file)
    
    st.write("Uploaded file preview:")
    st.dataframe(data.head())
    
    # Store the data in session state for later use
    st.session_state["file_data"] = data.to_dict(orient="records")

# Chat input and response display
user_input = st.text_input("Your question:", key="input")
if user_input:
    # Store user message
    st.session_state["messages"].append({"role": "user", "content": user_input})
    
    # Generate response
    response = analyze_and_respond(user_input)
    st.session_state["messages"].append({"role": "assistant", "content": response})
    
    # Display conversation
    for message in st.session_state["messages"]:
        if message["role"] == "user":
            st.write(f"**You:** {message['content']}")
        else:
            st.write(f"**Bot:** {message['content']}")
