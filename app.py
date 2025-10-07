# app.py

import streamlit as st
import torch
import pickle
from transformers import DistilBertTokenizer, DistilBertForSequenceClassification
import os
from baristabox.engines.doctor_engine import CoffeeDoctor
from baristabox.engines.sommelier_engine import CoffeeSommelier
from baristabox.engines.brewer_engine import MasterBrewer

# --- CONFIGURATION ---
INTENT_MODEL_PATH = 'models/main_intent_classifier_pytorch'
DOCTOR_MODEL_PATH = 'models/doctor_problem_classifier_pytorch'
BEANS_DATA_PATH = 'datasets/coffee_beans.json'
RECIPES_DATA_PATH = 'datasets/brew_recipes.json'
KNOWLEDGE_BASE_PATH = 'datasets/troubleshooting_knowledge_base.json'

# --- MODEL LOADING (with caching) ---
# This decorator ensures that our models and engines are loaded only once, making the app faster.
@st.cache_resource
def load_models_and_engines():
    """Loads all necessary models, tokenizers, and engines."""
    # Load Intent Classifier
    intent_tokenizer = DistilBertTokenizer.from_pretrained(INTENT_MODEL_PATH)
    intent_model = DistilBertForSequenceClassification.from_pretrained(INTENT_MODEL_PATH)
    with open(os.path.join(INTENT_MODEL_PATH, 'label_encoder.pkl'), 'rb') as f:
        intent_label_encoder = pickle.load(f)

    # Load Doctor Problem Classifier
    doctor_tokenizer = DistilBertTokenizer.from_pretrained(DOCTOR_MODEL_PATH)
    doctor_model = DistilBertForSequenceClassification.from_pretrained(DOCTOR_MODEL_PATH)
    with open(os.path.join(DOCTOR_MODEL_PATH, 'label_encoder.pkl'), 'rb') as f:
        doctor_label_encoder = pickle.load(f)

    # Load Coffee Doctor Engine (Gemini RAG)
    gemini_api_key = st.secrets["GEMINI_API_KEY"]
    doctor_engine = CoffeeDoctor(KNOWLEDGE_BASE_PATH, gemini_api_key)
    sommelier_engine = CoffeeSommelier(BEANS_DATA_PATH, gemini_api_key)
    brewer_engine = MasterBrewer(BEANS_DATA_PATH, RECIPES_DATA_PATH, gemini_api_key)
    
    return {
        "intent": (intent_model, intent_tokenizer, intent_label_encoder),
        "doctor": (doctor_model, doctor_tokenizer, doctor_label_encoder),
        "doctor_engine": doctor_engine,
        "sommelier_engine": sommelier_engine,
        "brewer_engine": brewer_engine
    }

def predict_class(text, model, tokenizer, label_encoder):
    """Predicts the class of a given text using a loaded PyTorch model."""
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=64)
    with torch.no_grad():
        logits = model(**inputs).logits
    predicted_class_id = torch.argmax(logits, dim=1).item()
    predicted_class_label = label_encoder.inverse_transform([predicted_class_id])[0]
    return predicted_class_label

# --- STREAMLIT APP ---

# --- Page Configuration ---
st.set_page_config(
    page_title="BaristaBox AI",
    page_icon="☕",
    layout="centered"
)

st.title("☕ BaristaBox AI")
st.caption("Your personal AI coffee concierge. Ask me for a recommendation, a recipe, or help with a bad brew.")

# --- Load resources ---
resources = load_models_and_engines()

# --- Initialize Session State ---
# This is like the app's memory for a specific user session.
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hi there! How can I help you with your coffee today?"}]

if "chat_mode" not in st.session_state:
    st.session_state.chat_mode = "intent_classifier" # Start by trying to figure out the user's intent

# --- Display Chat History ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- Handle User Input ---
if prompt := st.chat_input("What's on your mind?"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # --- Main Logic: The Orchestrator ---
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            
            # --- STAGE 1: INTENT CLASSIFICATION ---
            if st.session_state.chat_mode == "intent_classifier":
                # Use the fast, local model to determine what the user wants
                intent_model, intent_tokenizer, intent_label_encoder = resources["intent"]
                user_intent = predict_class(prompt, intent_model, intent_tokenizer, intent_label_encoder)
                
                if user_intent == "doctor":
                    # --- STAGE 2: PROBLEM CLASSIFICATION (for Doctor) ---
                    st.session_state.chat_mode = "doctor_chat" # Switch mode
                    
                    # Use the second local model to find the specific problem
                    doctor_model, doctor_tokenizer, doctor_label_encoder = resources["doctor"]
                    problem = predict_class(prompt, doctor_model, doctor_tokenizer, doctor_label_encoder)

                    # --- STAGE 3: START GEMINI-POWERED DIAGNOSIS ---
                    doctor_engine = resources["doctor_engine"]
                    # Start the RAG conversation with Gemini
                    response = doctor_engine.start_diagnosis(problem)
                    st.markdown(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})

                # --- (Placeholder for future modules) ---
                elif user_intent == "sommelier":
                    # --- START SEMANTIC SEARCH & RAG RECOMMENDATION ---
                    sommelier_engine = resources["sommelier_engine"]
                    response = sommelier_engine.get_recommendation(prompt)
                    
                    st.markdown(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    # Reset chat_mode so the next message is treated as a new intent
                    # st.session_state.chat_mode = "intent_classifier"
                
                elif user_intent == "master_brewer":
                    # --- START ENTITY EXTRACTION & RAG RECIPE ---
                    brewer_engine = resources["brewer_engine"]
                    response = brewer_engine.get_recipe(prompt)
                    
                    st.markdown(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    # Reset chat_mode so the next message is treated as a new intent
                    # st.session_state.chat_mode = "intent_classifier"
                
                else:
                    response = "I'm not quite sure how to help with that yet. Try asking me to help fix your coffee!"
                    st.markdown(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})

            # --- STAGE 4: CONTINUE DOCTOR CONVERSATION ---
            elif st.session_state.chat_mode == "doctor_chat":
                # The conversation is already ongoing, so just pass the prompt to the engine
                doctor_engine = resources["doctor_engine"]
                response = doctor_engine.continue_conversation(prompt)
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})