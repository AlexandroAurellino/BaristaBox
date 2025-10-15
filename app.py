# app.py (Version with Context-Aware Doctor Logic)

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
@st.cache_resource
def load_models_and_engines():
    """Loads all necessary models, tokenizers, and engines."""
    gemini_api_key = st.secrets["GEMINI_API_KEY"]
    
    # Load Classifiers
    intent_tokenizer = DistilBertTokenizer.from_pretrained(INTENT_MODEL_PATH)
    intent_model = DistilBertForSequenceClassification.from_pretrained(INTENT_MODEL_PATH)
    with open(os.path.join(INTENT_MODEL_PATH, 'label_encoder.pkl'), 'rb') as f:
        intent_label_encoder = pickle.load(f)

    doctor_tokenizer = DistilBertTokenizer.from_pretrained(DOCTOR_MODEL_PATH)
    doctor_model = DistilBertForSequenceClassification.from_pretrained(DOCTOR_MODEL_PATH)
    with open(os.path.join(DOCTOR_MODEL_PATH, 'label_encoder.pkl'), 'rb') as f:
        doctor_label_encoder = pickle.load(f)

    # Load Engines
    doctor_engine = CoffeeDoctor(BEANS_DATA_PATH, RECIPES_DATA_PATH, KNOWLEDGE_BASE_PATH, gemini_api_key)
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
    """Predicts the class of a given text."""
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=64)
    with torch.no_grad():
        logits = model(**inputs).logits
    predicted_class_id = torch.argmax(logits, dim=1).item()
    return label_encoder.inverse_transform([predicted_class_id])[0]

# --- STREAMLIT APP ---

st.set_page_config(page_title="BaristaBox AI", page_icon="☕", layout="centered")
st.title("☕ BaristaBox AI")
st.caption("Your personal AI coffee concierge.")

resources = load_models_and_engines()

# --- Initialize Session State ---
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hi there! How can I help you with your coffee today?"}]

if "chat_mode" not in st.session_state:
    st.session_state.chat_mode = "intent_classifier"

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- Handle User Input ---
if prompt := st.chat_input("What's on your mind?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # --- Main Logic: The Orchestrator ---
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = ""
            
            # --- STAGE 1: INTENT CLASSIFICATION ---
            if st.session_state.chat_mode == "intent_classifier":
                intent_model, intent_tokenizer, intent_label_encoder = resources["intent"]
                user_intent = predict_class(prompt, intent_model, intent_tokenizer, intent_label_encoder)
                print(f"[Orchestrator] Intent classified as: '{user_intent}'")

                if user_intent == "doctor":
                    st.session_state.chat_mode = "doctor_chat"
                    
                    doctor_model, doctor_tokenizer, doctor_label_encoder = resources["doctor"]
                    problem = predict_class(prompt, doctor_model, doctor_tokenizer, doctor_label_encoder)
                    print(f"[Orchestrator] Problem classified as: '{problem}'")

                    doctor_engine = resources["doctor_engine"]
                    response = doctor_engine.start_diagnosis_flow(problem, user_query=prompt)
                
                elif user_intent == "sommelier":
                    sommelier_engine = resources["sommelier_engine"]
                    response = sommelier_engine.get_recommendation(prompt)
                
                elif user_intent == "master_brewer":
                    brewer_engine = resources["brewer_engine"]
                    response = brewer_engine.get_recipe(prompt)
                
                else:
                    response = "I'm not quite sure how to help with that. Try asking me about a bad brew or for a recommendation."

            # --- STAGE 2: HANDLE ONGOING DOCTOR CONVERSATION ---
            elif st.session_state.chat_mode == "doctor_chat":
                doctor_engine = resources["doctor_engine"]
                response = doctor_engine.process_next_step(prompt)
                
                # If the diagnosis is over, reset the chat mode
                if doctor_engine.state is None:
                    st.session_state.chat_mode = "intent_classifier"
            
            # Display the final response
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})