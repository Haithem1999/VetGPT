import streamlit as st
import os
from openai import OpenAI
import uuid 
import json
from PyPDF2 import PdfReader
from docx import Document

# Initialize conversation history in session state if not present
if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = {}
if 'current_conversation' not in st.session_state:
    st.session_state.current_conversation = []
if 'selected_conversation' not in st.session_state:
    st.session_state.selected_conversation = None


# Initialize session state for chat history
if 'messages' not in st.session_state:
    st.session_state.messages = []


# Set up the OpenAI API key
api_key = st.secrets["OPENAI_API_KEY"]
client = OpenAI(api_key=api_key)

# Streamlit app
st.title("Veterinarian Chatbot")
st.write("Welcome to the Veterinarian Chatbot. How can I assist you with your pet's health today?")


# Store uploaded documents in session state
if 'documents' not in st.session_state:
    st.session_state.documents = {}
    st.session_state.current_context = ""  # Initialize as empty string
    st.session_state.uploaded_file = None  # Initialize uploaded file as None

# Create a unique session ID for the current user
if 'session_id' not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

# File upload
uploaded_file = st.file_uploader("Upload a file", type=["pdf", "docx", "txt"], key="file_uploader")

# If a file is uploaded, process it and store its content
if uploaded_file:
    st.session_state.uploaded_file = uploaded_file  # Store uploaded file in session state
    if uploaded_file.type == "application/pdf":
        pdf_reader = PdfReader(uploaded_file)
        text = "".join([page.extract_text() for page in pdf_reader.pages])
        st.session_state.current_context = text  # Store parsed text for chatbot use
    elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        doc = Document(uploaded_file)
        text = "\n".join([para.text for para in doc.paragraphs])
        st.session_state.current_context = text  # Store parsed text for chatbot use
    elif uploaded_file.type == "text/plain":
        text = uploaded_file.read().decode("utf-8")
        st.session_state.current_context = text  # Store parsed text for chatbot use
    else:
        text = "Unsupported file format."

# Initialize toggle state in session state
if "show_content" not in st.session_state:
    st.session_state.show_content = False

# Layout for buttons in a single row using container
with st.container():
    col1, spacer, col2 = st.columns([1, 1.15, 1])  # Equal-width columns to align buttons

    with col1:
        # Toggle button to display or hide content
        if st.button(" 📝 Show/Hide File Content", key="show_hide_button"):
            st.session_state.show_content = not st.session_state.show_content

    with col2:
        # Download button for conversation
        st.download_button(
            " ⬇️ Download Conversation",
            data=json.dumps(st.session_state.messages, indent=2),
            file_name= f"Conversation_{st.session_state.session_id[:7]}.json",
            mime="application/json", 
            key="download_button"
        )

    
# Display or hide content based on the toggle state
if uploaded_file and st.session_state.show_content:
    st.write(text)


# Add space between buttons and chat section
st.write("")  
st.write("") 
st.write("") 


# Function to generate response
def generate_response(prompt):
    # Define the system prompt
    system_prompt = """ You are a specialized virtual assistant designed to help pet owners understand and manage their pet's health and well-being. 
                        Your role is to provide accurate, reliable, and timely information on pet-related health issues, such as symptoms, causes, 
                        home care, preventive tips, and when to seek veterinary care.
                        
                        ### Conversation Flow:
                        At the start of every conversation, collect details in a friendly, conversational, and sequential manner:
                        1. Owner's name  
                        2. Pet's name and age  
                        3. Pet's breed (include a kind compliment to make the user feel welcomed).  
                        4. Owner's email (for follow-ups).  
                        
                        Once the details are gathered, proceed to address their specific needs.
                        
                        ### Key Capabilities:  
                        - Health Insights: Suggest potential causes based on symptoms.  
                        - Home Remedies: Provide safe first aid or home care solutions.  
                        - When to Seek Help: Advise users to visit a vet for serious concerns.  
                        - Preventive Care: Share tips on diet, exercise, and routine check-ups.  
                        - Behavioral Advice: Help address common behavioral issues with training or management techniques.
                        
                        ### Tone and Style:  
                        - Supportive, calm, and empathetic.  
                        - Responses should be concise, practical, and informative.  
                        - After each answer, ask a relevant follow-up question to keep the user engaged.  
                        
                        ### Language:  
                        Communicate primarily in French. If the user prefers English, switch accordingly.
                        """


    if st.session_state.current_context:
        user_prompt = f"{prompt}\n\nDocument content for reference: {st.session_state.current_context}"
    else:
        user_prompt = prompt

    response = client.chat.completions.create(
        model="ft:gpt-4o-mini-2024-07-18:personal::Aa7eN5z8",
        messages=[{"role": "system", "content": system_prompt}] + st.session_state.messages + [{"role": "user", "content": user_prompt}],
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

# Load previous messages for this session, if any
if st.session_state.session_id in conversations:
    st.session_state.messages = conversations[st.session_state.session_id]

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Initialize sidebar for conversation history
st.sidebar.title("Add a New Conversation")

# Create a "New Conversation" button
if st.sidebar.button("➕ New Conversation"):
    # Clear the current conversation
    st.session_state.messages = []
    # Generate new session ID
    st.session_state.session_id = str(uuid.uuid4())
    # Clear current context and uploaded file when starting a new conversation
    st.session_state.current_context = ""  # Clear document content
    st.session_state.uploaded_file = None  # Clear uploaded file
    st.rerun()
    
st.sidebar.write("")

st.sidebar.title("Conversation History")

# Display past conversations in sidebar
for session_id, msgs in conversations.items():
    if msgs:  # Only show sessions that have messages
        # Get first user message as title, or use session ID if no messages
        # title = next((msg["content"][:30] + "..." for msg in msgs if msg["role"] == "user"), f"Conversation {session_id[:8]}")
        title = f"Conversation_{session_id[:7]}"
        if st.sidebar.button(title, key=session_id):
            st.session_state.session_id = session_id
            st.session_state.messages = msgs
            st.rerun()

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
