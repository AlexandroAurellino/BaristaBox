import json
import os
import google.generativeai as genai

class CoffeeDoctor:
    def __init__(self, knowledge_base_path, gemini_api_key):
        """
        Initializes the CoffeeDoctor with the knowledge base and Gemini API.
        """
        if not os.path.exists(knowledge_base_path):
            raise FileNotFoundError(f"Knowledge base file not found at: {knowledge_base_path}")
            
        with open(knowledge_base_path, 'r') as f:
            self.knowledge_base = json.load(f)
        
        # Configure the Gemini API
        genai.configure(api_key=gemini_api_key)
        # Use correct model name - choose one of these options:
        # Option 1: Latest stable Gemini 2.5 Flash (recommended for performance)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        
        # Alternative options you can use instead:
        # Option 2: Gemini 2.0 Flash (good balance of features and cost)
        # self.model = genai.GenerativeModel('gemini-2.0-flash')
        
        # Option 3: Gemini 1.5 Flash (if you need to stick with 1.5)
        # self.model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Option 4: Specific stable version (recommended for production)
        # self.model = genai.GenerativeModel('gemini-2.5-flash-001')
        
        self.chat = None # Will hold the conversation chat object
        print("Coffee Doctor engine (Gemini RAG) initialized successfully!")

    def start_diagnosis(self, problem):
        """
        Starts a new diagnostic chat session with Gemini, providing the relevant knowledge.
        """
        if problem not in self.knowledge_base:
            return "Sorry, I don't have information on that specific coffee problem. Could you describe it differently?"

        # Retrieve the relevant knowledge for the identified problem
        retrieved_knowledge = self.knowledge_base[problem]
        knowledge_context = json.dumps(retrieved_knowledge, indent=2)

        # Augment the initial system prompt with the retrieved knowledge
        system_prompt = f"""
        You are 'The Coffee Doctor,' a world-class barista and a friendly, helpful AI expert. 
        Your goal is to diagnose a user's coffee brewing problem based *only* on the trusted knowledge I provide below.
        
        Follow these rules strictly:
        1.  Start the conversation by empathizing with the user and stating the likely problem based on the 'description' field.
        2.  Guide the user through the diagnosis by asking the 'question' for the *first* cause listed in the knowledge.
        3.  Do NOT list all the questions at once. Ask one question at a time.
        4.  Wait for the user's response before proceeding.
        5.  Be conversational, clear, and encouraging. Do not use technical jargon unless it's in the knowledge base.
        6.  Your entire reasoning MUST be based on the provided JSON knowledge. Do not invent causes or solutions.

        --- TRUSTED KNOWLEDGE BASE for '{problem}' ---
        {knowledge_context}
        --- END OF KNOWLEDGE BASE ---
        """

        # Start a new chat session with the system prompt
        self.chat = self.model.start_chat(history=[
            {'role': 'user', 'parts': [system_prompt]},
            {'role': 'model', 'parts': ["I understand. Let's get to the bottom of this. What seems to be the problem with your coffee?"]}
        ])

        # Generate the first response from the model to kick off the conversation
        initial_user_message = f"My coffee tastes {problem}."
        model_response = self.chat.send_message(initial_user_message)
        
        return model_response.text

    def continue_conversation(self, user_input):
        """
        Sends the user's next message to the ongoing chat and gets the model's response.
        """
        if not self.chat:
            return "Sorry, we need to start a diagnosis first."
        
        model_response = self.chat.send_message(user_input)
        return model_response.text

# --- This block is for simple, direct testing of the engine ---
if __name__ == '__main__':
    # You would need to set up your GOOGLE_API_KEY as an environment variable
    # for this direct test to work.
    # For now, we will test this through the Streamlit app.
    print("This script is not meant to be run directly anymore.")
    print("Please test the CoffeeDoctor engine through the main `app.py`.")