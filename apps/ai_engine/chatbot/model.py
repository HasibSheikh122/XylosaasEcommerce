# apps/ai_engine/chatbot/model.py
import json
import random
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class ChatbotModel:
    def __init__(self, tenant_id):
        self.tenant_id = tenant_id
        self.intents = self._load_intents()
        self.vectorizer = TfidfVectorizer()
        self._train()
    
    def _load_intents(self):
        """Load intent patterns from database"""
        # Load from DB
        pass
    
    def _train(self):
        """Train the chatbot model"""
        patterns = []
        tags = []
        
        for intent in self.intents:
            for pattern in intent['patterns']:
                patterns.append(pattern)
                tags.append(intent['tag'])
        
        self.vectorizer.fit(patterns)
        self.pattern_vectors = self.vectorizer.transform(patterns)
        self.tags = tags
    
    def get_response(self, message):
        """Get chatbot response for user message"""
        # Vectorize the message
        message_vector = self.vectorizer.transform([message])
        
        # Find most similar pattern
        similarities = cosine_similarity(message_vector, self.pattern_vectors)
        best_match_idx = np.argmax(similarities)
        
        if similarities[0][best_match_idx] > 0.3:
            tag = self.tags[best_match_idx]
            # Find intent and return random response
            for intent in self.intents:
                if intent['tag'] == tag:
                    return random.choice(intent['responses']), tag
        
        return "I'm not sure how to help with that. Can you rephrase?", "unknown"