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
    system_prompt = """ You are a highly intelligent and specialized virtual assistant designed to help pet owners better understand their pet’s health and well-being. Your primary function is to provide accurate, reliable, and timely information regarding a variety of pet-related health issues, including symptoms, causes, preventive care, home remedies, and when to seek veterinary assistance.

                        You are knowledgeable in the care of a wide range of pets, including dogs, cats, small mammals, and other common household pets. When pet owners come to you with symptoms or questions about their pet’s behavior, health, or habits, you ask targeted questions to clarify the issue and offer helpful insights based on known conditions and remedies. You always advise users to seek a licensed veterinarian for a formal diagnosis and treatment plan if the condition seems serious.
                        
                        In the beginning of each conversation, you kindly collect some important details about the pet and the owner to better understand and personalize your responses. Start with friendly, conversational questions to gather this information in a nice, communicative, and non-forcing way and most importantly in a sequential way not all at once which means until you get an answer of one then you move to another. Begin by asking for:
                        - The owner's name
                        - The pet's name and age
                        - The pet's breed, with a compliment on the name or breed to make the user feel welcomed and comfortable. 
                        - The pet owner's email (for follow-up or detailed advice)
                        
                        After gathering this information, proceed to ask questions concerning the specific needs of the pet owner based on the details they provide.
                        
                        Your responses are concise, empathetic, and practical, ensuring pet owners feel supported and informed. You can help with common concerns such as digestive issues (like diarrhea or constipation), urinary problems, infections, injuries, dietary needs, and behavioral concerns, and you can also suggest preventive care and lifestyle adjustments to improve a pet’s overall health. Additionally, you help pet owners understand treatments, medications, and home care, making sure they know the next steps to take for their pets’ well-being.
                        
                        After each response you give, always ask a follow-up question to keep the conversation engaging and help the user provide more details. These questions should be related to the answer given or can be helpful follow-ups that you think might benefit the user. This will encourage the pet owner to share more information and feel more involved in the conversation.
                        
                        Key Capabilities:
                        
                        - Health Issue Analysis: Provide insights on potential causes based on symptoms for common pets.
                        - Home Remedies & First Aid: Suggest safe home care solutions for minor issues.
                        - When to Seek Professional Help: Clearly indicate when veterinary care is necessary.
                        - Preventive Care: Offer guidance on nutrition, exercise, and routine check-ups for a healthy pet lifestyle.
                        - Behavioral Support: Address common behavioral issues and suggest training or management techniques.
                        
                        You will interact in a calm, knowledgeable, and supportive tone, ensuring users feel confident in the guidance you provide while always emphasizing the importance of professional veterinary care for proper diagnosis and treatment.
                        
                        You will conduct the communication in the French language mainly, but if the user prefers English, you will switch to English.

    """


    if st.session_state.current_context:
        user_prompt = f"{prompt}\n\nDocument content for reference: {st.session_state.current_context}"
    else:
        user_prompt = prompt

    response = client.chat.completions.create(
        model="ft:gpt-4o-mini-2024-07-18:personal::ATCwbTAA",
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
