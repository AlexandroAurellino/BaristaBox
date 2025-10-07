# baristabox/engines/brewer_engine.py

import json
import os
import google.generativeai as genai
import re

class MasterBrewer:
    def __init__(self, beans_data_path, recipes_data_path, gemini_api_key):
        """
        Initializes the MasterBrewer.
        """
        if not os.path.exists(beans_data_path):
            raise FileNotFoundError(f"Bean data file not found at: {beans_data_path}")
        if not os.path.exists(recipes_data_path):
            raise FileNotFoundError(f"Recipe data file not found at: {recipes_data_path}")
            
        with open(beans_data_path, 'r', encoding='utf-8') as f:
            self.beans_data = json.load(f)
        with open(recipes_data_path, 'r', encoding='utf-8') as f:
            self.recipes_data = json.load(f)

        # Create mappings for easy lookups
        self.bean_name_to_id = {bean['name'].lower(): bean['id'] for bean in self.beans_data}
        self.known_brew_methods = ["v60", "aeropress", "french press", "chemex", "kalita wave"]

        # Configure the Gemini API
        genai.configure(api_key=gemini_api_key)
        self.gemini_model = genai.GenerativeModel('gemini-2.5-flash')
        
        print("Master Brewer engine (Entity Extraction & Gemini RAG) initialized successfully!")

    def _extract_entities(self, user_query):
        """
        Extracts the coffee bean name and brew method from the user's query.
        """
        query_lower = user_query.lower()
        found_bean_name = None
        found_brew_method = None

        # Search for a known bean name in the query
        for bean_name in self.bean_name_to_id.keys():
            if bean_name in query_lower:
                found_bean_name = bean_name
                break # Stop after finding the first match

        # Search for a known brew method in the query
        for method in self.known_brew_methods:
            if method in query_lower:
                found_brew_method = method
                break
        
        return found_bean_name, found_brew_method

    def get_recipe(self, user_query):
        """
        Orchestrates the RAG process for getting a brew recipe.
        """
        # 1. Extract Entities
        bean_name, brew_method = self._extract_entities(user_query)

        if not bean_name or not brew_method:
            return "I can certainly help with a recipe! Please tell me which coffee bean and which brew method you'd like to use (for example, 'recipe for Ethiopia Yirgacheffe with a V60')."

        # 2. Retrieve: Find the matching recipe
        target_bean_id = self.bean_name_to_id.get(bean_name)
        found_recipe = None
        if target_bean_id:
            for recipe in self.recipes_data:
                if recipe['bean_id'] == target_bean_id and recipe['brew_method'].lower() == brew_method:
                    found_recipe = recipe
                    break
        
        if not found_recipe:
            return f"I'm sorry, I don't have a specific recipe for '{bean_name.title()}' with a '{brew_method.title()}' right now. I'll ask my expert to add one soon!"

        retrieved_knowledge = json.dumps(found_recipe, indent=2)

        # 3. Augment: Build a detailed prompt for Gemini
        system_prompt = f"""
        You are 'The Master Brewer,' a precise, clear, and encouraging AI coffee expert.
        Your goal is to provide a user with a step-by-step brew recipe based ONLY on the JSON data I provide.

        Follow these rules strictly:
        1.  Start by confirming the recipe you are providing (e.g., "Certainly! Here is the expert recipe for...").
        2.  Present the core parameters (Grind Size, Coffee Dose, Water Amount, Water Temperature) as a clear, easy-to-read list.
        3.  Translate the raw data into a friendly, step-by-step guide.
        4.  Incorporate the 'technique_notes' into the steps to give it an expert touch.
        5.  Finish with an encouraging closing statement (e.g., "Enjoy your perfectly brewed cup!").
        
        --- USER's REQUEST ---
        "{user_query}"

        --- EXACT RECIPE DATA (Your knowledge base) ---
        {retrieved_knowledge}
        --- END OF KNOWLEDGE BASE ---
        """
        
        # 4. Generate: Call the Gemini API
        try:
            response = self.gemini_model.generate_content(system_prompt)
            return response.text
        except Exception as e:
            print(f"An error occurred with the Gemini API: {e}")
            return "I'm having a little trouble retrieving that recipe right now. Please try again in a moment."