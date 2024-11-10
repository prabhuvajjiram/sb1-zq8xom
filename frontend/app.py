import streamlit as st
import requests
import json
from datetime import datetime

API_URL = "http://localhost:8000"

st.set_page_config(layout="wide")
st.title("Document Management & Chat System")

# Initialize session state for chat history
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# Sidebar for document management
with st.sidebar:
    st.header("Document Management")
    
    # Upload document
    uploaded_file = st.file_uploader("Upload Document", type=['txt', 'pdf', 'doc', 'docx'])
    if uploaded_file:
        files = {"file": uploaded_file}
        response = requests.post(f"{API_URL}/upload", files=files)
        if response.status_code == 200:
            st.success("Document uploaded successfully!")
        else:
            st.error("Error uploading document")
    
    # List documents
    st.subheader("Existing Documents")
    response = requests.get(f"{API_URL}/documents")
    if response.status_code == 200:
        documents = response.json()
        for doc in documents:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(doc['name'])
            with col2:
                if st.button("Delete", key=doc['id']):
                    del_response = requests.delete(f"{API_URL}/documents/{doc['id']}")
                    if del_response.status_code == 200:
                        st.success("Document deleted!")
                        st.rerun()

# Main chat interface
st.header("Chat Interface")

# Display chat history
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# Chat input
if prompt := st.chat_input("Ask a question about your documents"):
    # Add user message to chat history
    st.session_state.chat_history.append({"role": "user", "content": prompt})
    
    # Get response from API
    response = requests.post(
        f"{API_URL}/chat",
        json={"message": prompt}
    )
    
    if response.status_code == 200:
        response_data = response.json()
        # Add assistant response to chat history
        st.session_state.chat_history.append({"role": "assistant", "content": response_data["response"]})
        
        # Show context if available
        if response_data.get("context"):
            with st.expander("Source Context"):
                st.write(response_data["context"])
    else:
        st.error("Error getting response from the server")