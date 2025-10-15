# baristabox/engines/doctor_engine.py (Version 4.0 - Recipe-Driven Diagnosis)

import json
import os
import google.generativeai as genai
import re

class CoffeeDoctor:
    def __init__(self, beans_data_path, recipes_data_path, knowledge_base_path, gemini_api_key):
        """
        Initializes the Recipe-Driven, Context-Aware, Rule-Based CoffeeDoctor.
        """
        # Load all three knowledge bases
        with open(beans_data_path, 'r', encoding='utf-8') as f:
            self.beans_data = json.load(f)
        with open(recipes_data_path, 'r', encoding='utf-8') as f:
            self.recipes_data = json.load(f)
        with open(knowledge_base_path, 'r', encoding='utf-8') as f:
            self.knowledge_base = json.load(f)
        
        genai.configure(api_key=gemini_api_key)
        self.gemini_model = genai.GenerativeModel('gemini-2.5-flash')
        
        # Internal state for the entire process
        self.state = None
        self.user_context = {}
        self.ideal_recipe = None # Will hold the ideal recipe if found
        self.cause_iterator = None
        self.current_cause_data = None
        
        print("Coffee Doctor engine (Recipe-Driven v4.0) initialized successfully!")

    def _phrase_with_gemini(self, prompt):
        """Helper to get a phrased response from Gemini."""
        try:
            response = self.gemini_model.generate_content(prompt)
            return response.text.strip().replace('"', '')
        except Exception as e:
            print(f"An error occurred with the Gemini API: {e}")
            return "I'm having a little trouble communicating right now. Please try again."

    def start_diagnosis_flow(self, problem, user_query):
        """Kicks off the multi-step diagnosis, starting with context gathering."""
        self.state = 'GATHERING_BEAN'
        self.user_context['problem'] = problem
        self.user_context['original_query'] = user_query
        print(f"[Doctor Engine] Starting diagnosis flow for problem: '{problem}'. State: {self.state}")
        prompt = "You are 'The Coffee Doctor.' Start a diagnosis for a user by first asking what coffee bean they are brewing. Explain that this will help you give a more precise diagnosis."
        return self._phrase_with_gemini(prompt)

    def process_next_step(self, user_response):
        """The main router function that handles the conversation flow based on the current state."""
        if self.state == 'GATHERING_BEAN':
            self.user_context['bean_name'] = user_response
            self.state = 'GATHERING_METHOD'
            print(f"[Doctor Engine] Context gathered: bean_name='{user_response}'. State: {self.state}")
            prompt = "You are 'The Coffee Doctor.' Ask the user what brew method they are using."
            return self._phrase_with_gemini(prompt)

        elif self.state == 'GATHERING_METHOD':
            self.user_context['brew_method'] = user_response
            self.state = 'DIAGNOSING'
            print(f"[Doctor Engine] Context gathered: brew_method='{user_response}'. State: {self.state}")
            return self._start_rule_based_diagnosis()

        elif self.state == 'DIAGNOSING':
            return self._process_diagnostic_response(user_response)
        
        else:
            return "I seem to have lost my train of thought. Let's start over. What's the problem with your coffee?"

    def _find_ideal_recipe(self):
        """Internal method to find the matching recipe based on user context."""
        bean_name = self.user_context.get('bean_name', '').lower()
        brew_method = self.user_context.get('brew_method', '').lower()
        
        # Find the bean_id from the name
        found_bean_id = None
        for bean in self.beans_data:
            if bean['name'].lower() in bean_name:
                found_bean_id = bean['id']
                break
        
        if not found_bean_id:
            print("[Doctor Engine] Could not find a matching bean in the database.")
            return None
            
        # Find the recipe using bean_id and brew_method
        for recipe in self.recipes_data:
            if recipe['bean_id'] == found_bean_id and recipe['brew_method'].lower() in brew_method:
                print(f"[Doctor Engine] Found ideal recipe: {recipe['recipe_id']}")
                return recipe
        
        print("[Doctor Engine] No specific recipe found for this combination.")
        return None

    def _start_rule_based_diagnosis(self):
        """Starts the diagnosis, now with recipe context."""
        self.ideal_recipe = self._find_ideal_recipe()
        
        problem = self.user_context['problem']
        problem_data = self.knowledge_base[problem]
        self.cause_iterator = iter(problem_data['causes'].items())
        
        print("[Doctor Engine] Context is complete. Starting rule-based diagnosis.")
        return self._ask_next_question() # Directly ask the first question

    def _ask_next_question(self):
        """Asks the next question, now making it comparative if a recipe exists."""
        try:
            cause_key, cause_data = next(self.cause_iterator)
            self.current_cause_data = cause_data
            print(f"[Doctor Engine] Testing cause: '{cause_key}'")
            
            question = cause_data['question']
            
            # --- NEW RECIPE-DRIVEN LOGIC ---
            # Modify the question based on the ideal recipe
            if self.ideal_recipe:
                if cause_key == 'grind_coarse' or cause_key == 'grind_fine':
                    ideal_grind = self.ideal_recipe.get('grind_size', 'the recommended setting')
                    question = f"The ideal recipe for this coffee uses a '{ideal_grind}' grind. {question}"
                elif cause_key == 'brew_time_short' or cause_key == 'brew_time_long':
                    ideal_time = "the recommended time (e.g., 2:30 for V60)" # Simple extraction for now
                    if 'technique_notes' in self.ideal_recipe:
                        match = re.search(r'(\d+:\d+)', self.ideal_recipe['technique_notes'])
                        if match:
                            ideal_time = match.group(1)
                    question = f"The target brew time for this recipe is around {ideal_time}. {question}"
                elif cause_key == 'water_temp_low' or cause_key == 'water_temp_high':
                    ideal_temp = self.ideal_recipe.get('water_temp_c', 'the recommended temperature')
                    question = f"This recipe calls for water at {ideal_temp}°C. {question}"
            # --- END OF NEW LOGIC ---

            prompt = f"You are 'The Coffee Doctor.' Ask the user the following diagnostic question clearly and concisely. Do not add extra greetings."
            prompt += f"\nThe question to ask is: \"{question}\""
            return self._phrase_with_gemini(prompt)

        except StopIteration:
            self.state = None
            return "Hmm, I've gone through the common causes and couldn't find a match. It might be a more complex issue."

    def _process_diagnostic_response(self, user_response):
        """Processes the user's yes/no answer using an LLM to interpret the response."""
        # This function remains largely the same, but the 'solution' part can be enhanced.
        current_question = self.current_cause_data['question']
        interpretation_prompt = f"""
        Analyze the user's response in the context of the question that was asked.
        Question: "{current_question}"
        User's response: "{user_response}"
        Is the user confirming the premise of the question? Respond with ONLY one word: affirmative, negative, or unsure.
        """
        interpretation = self._phrase_with_gemini(interpretation_prompt).lower()
        print(f"[Doctor Engine] Interpretation: '{interpretation}'")

        if "affirmative" in interpretation:
            print("[Doctor Engine] Response interpreted as AFFIRMATIVE.")
            solution_text = self.current_cause_data['solution']
            recipe_context = f"Context: User is brewing '{self.user_context.get('bean_name', 'this coffee')}' with a '{self.user_context.get('brew_method', 'their brewer')}'."
            if self.ideal_recipe:
                recipe_context += f" The ideal recipe is: {json.dumps(self.ideal_recipe)}"

            prompt = f"""
            You are 'The Coffee Doctor.' The diagnosis is confirmed. Start with "Great, I think we've found the issue!".
            Then, explain the following solution in a helpful and encouraging way.
            Use the provided context to make your explanation more specific and tailored to the user's situation.

            {recipe_context}

            The solution to explain is:
            "{solution_text}"
            """
            solution_response = self._phrase_with_gemini(prompt)
            self.state = None
            return solution_response
        else:
            print(f"[Doctor Engine] Response interpreted as NEGATIVE/UNSURE. Moving to next cause.")
            return self._ask_next_question()