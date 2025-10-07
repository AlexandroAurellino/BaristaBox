import json
import os
import google.generativeai as genai
from sentence_transformers import SentenceTransformer, util
import torch

class CoffeeSommelier:
    def __init__(self, beans_data_path, gemini_api_key, embedding_model_name='all-MiniLM-L6-v2'):
        """
        Initializes the CoffeeSommelier.
        """
        if not os.path.exists(beans_data_path):
            raise FileNotFoundError(f"Bean data file not found at: {beans_data_path}")
            
        with open(beans_data_path, 'r', encoding='utf-8') as f:
            self.beans_data = json.load(f)

        # Configure the Gemini API
        genai.configure(api_key=gemini_api_key)
        self.gemini_model = genai.GenerativeModel('gemini-2.5-flash')

        # Load the sentence-transformer model for semantic search
        self.embedding_model = SentenceTransformer(embedding_model_name)
        
        # Pre-compute embeddings for all coffee beans upon initialization
        self._create_flavor_map()
        
        print("Coffee Sommelier engine (Semantic Search & Gemini RAG) initialized successfully!")

    def _create_flavor_map(self):
        """
        Creates a "flavor map" by generating embeddings for each coffee bean.
        This is a pre-computation step for fast semantic search.
        """
        print("Creating the coffee flavor map (computing embeddings)...")
        # For each bean, create a descriptive text combining tasting notes and tags
        corpus = [
            f"{bean['name']}. Tasting notes: {bean['tasting_notes']}. Best for those looking for something {', '.join(bean['expert_tags'])}."
            for bean in self.beans_data
        ]
        
        # Generate embeddings for the entire corpus. This is the "map".
        # We move this to the CPU to ensure it works on all systems.
        self.corpus_embeddings = self.embedding_model.encode(corpus, convert_to_tensor=True, device='cpu')
        print("Flavor map created.")

    def find_top_matches(self, user_query, top_k=3):
        """
        Finds the top_k most similar coffee beans to the user's query.
        """
        # Convert user's query into a vector (embedding)
        query_embedding = self.embedding_model.encode(user_query, convert_to_tensor=True, device='cpu')

        # Compute cosine similarity between the query and all coffee beans
        cos_scores = util.cos_sim(query_embedding, self.corpus_embeddings)[0]
        
        # Get the top_k scores and their indices
        top_results = torch.topk(cos_scores, k=min(top_k, len(self.beans_data)))

        # Return the actual bean data for the top matches
        return [self.beans_data[idx] for idx in top_results.indices]

    def get_recommendation(self, user_query):
        """
        Orchestrates the RAG process for getting a coffee recommendation.
        """
        # 1. Retrieve: Find the most relevant coffee beans using semantic search
        top_matches = self.find_top_matches(user_query)
        retrieved_knowledge = json.dumps(top_matches, indent=2)

        # 2. Augment: Build a detailed prompt for Gemini
        system_prompt = f"""
        You are 'The Coffee Sommelier,' a friendly, passionate, and knowledgeable AI coffee expert.
        Your goal is to give a personalized coffee recommendation to the user.
        
        Follow these rules strictly:
        1.  Base your recommendation ONLY on the JSON data of the top matching coffees I provide below.
        2.  Start with a friendly and engaging opening.
        3.  Recommend the #1 top match to the user. Explain WHY it's a great fit by connecting its 'tasting_notes' and 'expert_tags' directly to the user's query. Be specific.
        4.  Briefly mention one or two of the other top matches as alternative options.
        5.  Keep your response concise, persuasive, and easy to read.

        --- USER's PREFERENCE ---
        "{user_query}"

        --- TOP MATCHING COFFEES (Your knowledge base) ---
        {retrieved_knowledge}
        --- END OF KNOWLEDGE BASE ---
        """

        # 3. Generate: Call the Gemini API to get a conversational response
        try:
            response = self.gemini_model.generate_content(system_prompt)
            return response.text
        except Exception as e:
            print(f"An error occurred with the Gemini API: {e}")
            return "I'm having a little trouble thinking of a recommendation right now. Please try again in a moment."