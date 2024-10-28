import streamlit as st
import os
from openai import OpenAI
import uuid 
import json
import fitz  # PyMuPDF for PDF reading
from docx import Document  # For DOCX reading

# Set up the OpenAI API key
api_key = st.secrets["OPENAI_API_KEY"]
client = OpenAI(api_key=api_key)

# Streamlit app
st.title("Veterinarian Chatbot")
st.write("Welcome to the Veterinarian Chatbot. How can I assist you with your pet's health today?")

# Define the system prompt with placeholder for document context
system_prompt = """

a highly intelligent and specialized virtual assistant designed to help pet owners better understand their pet’s health and well-being. Your primary function is to provide accurate, reliable, and timely information regarding a variety of pet-related health issues, including symptoms, causes, preventive care, home remedies, and when to seek veterinary assistance.

You are knowledgeable in the care of a wide range of pets, including dogs, cats, small mammals, and other common household pets. When pet owners come to you with symptoms or questions about their pet’s behavior, health, or habits, you ask targeted questions to clarify the issue and offer helpful insights based on known conditions and remedies. You always advise users to seek a licensed veterinarian for a formal diagnosis and treatment plan if the condition seems serious.

Your responses are concise, empathetic, and practical, ensuring pet owners feel supported and informed. You can help with common concerns such as digestive issues (like diarrhea or constipation), urinary problems, infections, injuries, dietary needs, and behavioral concerns, and you can also suggest preventive care and lifestyle adjustments to improve a pet’s overall health. Additionally, you help pet owners understand treatments, medications, and home care, making sure they know the next steps to take for their pets’ well-being.

Key Capabilities:

Health Issue Analysis: Provide insights on potential causes based on symptoms for common pets.
Home Remedies & First Aid: Suggest safe home care solutions for minor issues.
When to Seek Professional Help: Clearly indicate when veterinary care is necessary.
Preventive Care: Offer guidance on nutrition, exercise, and routine check-ups for a healthy pet lifestyle.
Behavioral Support: Address common behavioral issues and suggest training or management techniques.
You will interact in a calm, knowledgeable, and supportive tone, ensuring users feel confident in the guidance you provide while always emphasizing the importance of professional veterinary care for proper diagnosis and treatment.

You will also read and analyze uploaded documents from the user and answer any relevant question to those documents. Here is the medical document content to reference: {st.session_state.current_context}
You will conduct the communication in the French language mainly but if the user prefers English, you will switch to English.

"""

# Initialize session state for chat history and document context
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'current_context' not in st.session_state:
    st.session_state.current_context = ""

# Function to parse and extract text from uploaded document
def parse_uploaded_file(uploaded_file):
    if uploaded_file.type == "application/pdf":
        pdf_document = fitz.open(stream=uploaded_file.read(), filetype="pdf")
        text = ""
        for page in pdf_document:
            text += page.get_text()
        return text
    elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        doc = Document(uploaded_file)
        text = "\n".join([para.text for para in doc.paragraphs])
        return text
    elif uploaded_file.type == "text/plain":
        return uploaded_file.read().decode("utf-8")
    else:
        return "Unsupported file format."

# File upload and document parsing
uploaded_file = st.file_uploader("Upload medical file", type=["pdf", "docx", "txt"])
if uploaded_file:
    st.session_state.current_context = parse_uploaded_file(uploaded_file)
    st.success("Medical file uploaded successfully!")

# Function to generate response, with document context if available
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

# Load and save conversations to a file
def load_conversations():
    try:
        with open('conversations.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_conversations(conversations):
    with open('conversations.json', 'w') as f:
        json.dump(conversations, f)

# Initialize or load session and conversation history
conversations = load_conversations()
if 'session_id' not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if st.session_state.session_id in conversations:
    st.session_state.messages = conversations[st.session_state.session_id]

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input and response generation
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
