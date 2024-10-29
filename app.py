import streamlit as st
import os
from openai import OpenAI
#from dotenv import load_dotenv
import uuid 
import json
from PyPDF2 import PdfReader
    

# Set up the OpenAI API key
# OPENAI API KEY

#api_key = os.getenv("OPENAI_API_KEY")
api_key = st.secrets["OPENAI_API_KEY"]

client = OpenAI(api_key= api_key)



# Streamlit app
st.title("Veterinarian Chatbot")
st.write("Welcome to the Veterinarian Chatbot. How can I assist you with your pet's health today?")


# -------------------------------------------------------

# Store uploaded documents in session state
if 'documents' not in st.session_state:
    st.session_state.documents = {}
    st.session_state.current_context = ""

# Initialize toggle state in session state
if "show_content" not in st.session_state:
    st.session_state.show_content = False

# Initialize session state for chat history
if 'messages' not in st.session_state:
    st.session_state.messages = []

# Toggle button to display or hide content
if st.button("Show/Hide File Content"):
    st.session_state.show_content = not st.session_state.show_content

# File upload
uploaded_file = st.file_uploader("Upload a file", type=["pdf", "docx", "txt"])

# Display content if toggled on
if uploaded_file and st.session_state.show_content:
    if uploaded_file.type == "application/pdf":
        pdf_reader = PdfReader(uploaded_file)
        text = "".join([page.extract_text() for page in pdf_reader.pages])
    elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        doc = Document(uploaded_file)
        text = "\n".join([para.text for para in doc.paragraphs])
    elif uploaded_file.type == "text/plain":
        text = uploaded_file.read().decode("utf-8")
    else:
        text = "Unsupported file format."

    # Display file content
    st.write(text)



# ---------------------------------------------------------


# Function to generate response with document context
def generate_response(prompt):
    prompt_with_context = system_prompt.format(st.session_state.current_context)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": prompt_with_context},
            *st.session_state.messages,
            {"role": "user", "content": prompt},
        ],
    )
    return response.choices[0].message.content


# Load previous conversations from a file
def load_conversations():
    try:
        with open('conversations.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

# Save conversations to a file
def save_conversations(conversations):
    with open('conversations.json', 'w') as f:
        json.dump(conversations, f)

# Load previous conversations
conversations = load_conversations()

# Create a unique session ID for the current user
if 'session_id' not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

# Load previous messages for this session, if any
if st.session_state.session_id in conversations:
    st.session_state.messages = conversations[st.session_state.session_id]

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("You:"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = generate_response(prompt)
        message_placeholder.markdown(full_response)
    
    st.session_state.messages.append({"role": "assistant", "content": full_response})
    
    # Save the updated conversation
    conversations[st.session_state.session_id] = st.session_state.messages
    save_conversations(conversations)


# # User input
# user_input = st.text_input("You:", "")

# if user_input:
#     # Generate response from OpenAI
#     response = client.chat.completions.create(
#         model="gpt-4o-mini",
#         messages=[
#             {"role": "system", "content": system_prompt},
#             {"role": "user", "content": user_input},
#         ],

#     )

#     # Display the response
#     st.write("VetBot:", response.choices[0].message.content)

# End Generation Here


