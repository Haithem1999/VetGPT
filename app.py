import streamlit as st
import os
from openai import OpenAI
#from dotenv import load_dotenv
import uuid 
import json
    
#load_dotenv()

# Set up the OpenAI API key
# OPENAI API KEY

#api_key = os.getenv("OPENAI_API_KEY")
api_key = st.secrets["OPENAI_API_KEY"]

client = OpenAI(api_key= api_key)



# Streamlit app
st.title("Veterinarian Chatbot")
st.write("Welcome to the Veterinarian Chatbot. How can I assist you with your pet's health today?")

# Define the system prompt
system_prompt = """a highly intelligent and specialized virtual assistant designed to help pet owners better understand their pet’s health and well-being. Your primary function is to provide accurate, reliable, and timely information regarding a variety of pet-related health issues, including symptoms, causes, preventive care, home remedies, and when to seek veterinary assistance.

You are knowledgeable in the care of a wide range of pets, including dogs, cats, small mammals, and other common household pets. When pet owners come to you with symptoms or questions about their pet’s behavior, health, or habits, you ask targeted questions to clarify the issue and offer helpful insights based on known conditions and remedies. You always advise users to seek a licensed veterinarian for a formal diagnosis and treatment plan if the condition seems serious.

Your responses are concise, empathetic, and practical, ensuring pet owners feel supported and informed. You can help with common concerns such as digestive issues (like diarrhea or constipation), urinary problems, infections, injuries, dietary needs, and behavioral concerns, and you can also suggest preventive care and lifestyle adjustments to improve a pet’s overall health. Additionally, you help pet owners understand treatments, medications, and home care, making sure they know the next steps to take for their pets’ well-being.

Key Capabilities:

Health Issue Analysis: Provide insights on potential causes based on symptoms for common pets.
Home Remedies & First Aid: Suggest safe home care solutions for minor issues.
When to Seek Professional Help: Clearly indicate when veterinary care is necessary.
Preventive Care: Offer guidance on nutrition, exercise, and routine check-ups for a healthy pet lifestyle.
Behavioral Support: Address common behavioral issues and suggest training or management techniques.
You will interact in a calm, knowledgeable, and supportive tone, ensuring users feel confident in the guidance you provide while always emphasizing the importance of professional veterinary care for proper diagnosis and treatment.
You will conduct the communication in the French language mainly but if the user prefers English, you will switch to English.
"""



# -------------------------------------------------------
# Initialize session state for document context and conversation persistence
if 'document_context' not in st.session_state:
    st.session_state.document_context = ""

# File paths for persistent storage
CONVERSATIONS_FILE = "conversations.json"
DOCUMENTS_FILE = "uploaded_documents.json"

def save_conversation(messages, document_context):
    """Save conversation history and document context to file"""
    conversation_data = {
        'messages': messages,
        'document_context': document_context,
        'timestamp': str(uuid.uuid4())
    }
    try:
        if os.path.exists(CONVERSATIONS_FILE):
            with open(CONVERSATIONS_FILE, 'r') as f:
                conversations = json.load(f)
        else:
            conversations = []
        conversations.append(conversation_data)
        with open(CONVERSATIONS_FILE, 'w') as f:
            json.dump(conversations, f)
    except Exception as e:
        st.error(f"Error saving conversation: {str(e)}")

def load_previous_conversations():
    """Load previous conversations from file"""
    try:
        if os.path.exists(CONVERSATIONS_FILE):
            with open(CONVERSATIONS_FILE, 'r') as f:
                return json.load(f)
        return []
    except Exception as e:
        st.error(f"Error loading conversations: {str(e)}")
        return []

# Function to process uploaded document
def process_document(file):
    if file.type == "application/pdf":
        # Process PDF file
        return file.getvalue().decode('utf-8', errors='ignore')
    elif file.type == "text/plain":
        # Process text file
        return file.getvalue().decode('utf-8')
    else:
        return file.getvalue().decode('utf-8', errors='ignore')

# Load previous conversations on startup
previous_conversations = load_previous_conversations()
if previous_conversations and 'messages' not in st.session_state:
    # Load the most recent conversation
    last_conversation = previous_conversations[-1]
    st.session_state.messages = last_conversation['messages']
    st.session_state.document_context = last_conversation['document_context']

# Add file uploader for medical documents
uploaded_file = st.file_uploader("Upload pet medical document", type=["txt", "pdf"])

if uploaded_file is not None:
    # Process the uploaded file
    document_content = process_document(uploaded_file)
    
    # Update the document context in session state
    st.session_state.document_context = f"Pet medical document content: {document_content}"
    
    # Save document context with current conversation
    save_conversation(st.session_state.messages, st.session_state.document_context)
    
    # Acknowledge the upload
    st.success("Document uploaded successfully. You can now ask questions about it.")







# ---------------------------------------------------------



# Initialize session state for chat history
if 'messages' not in st.session_state:
    st.session_state.messages = []

# Function to generate response
def generate_response(prompt):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
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
