# apps/ai_engine/recommendation/engine.py
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

class RecommendationEngine:
    def __init__(self, tenant_id):
        self.tenant_id = tenant_id
        self.collaborative = CollaborativeFiltering()
        self.content_based = ContentBasedFiltering()
    
    def get_recommendations(self, customer_id, product_id=None, limit=10):
        """Get personalized product recommendations"""
        # Hybrid approach: combine multiple algorithms
        cf_recs = self.collaborative.get_recommendations(customer_id)
        cb_recs = self.content_based.get_recommendations(product_id) if product_id else []
        
        # Combine and rank
        recommendations = self._combine_recommendations(cf_recs, cb_recs)
        return recommendations[:limit]
    
    def _combine_recommendations(self, cf_recs, cb_recs):
        """Combine recommendations from multiple sources"""
        # Weighted combination
        cf_weight = 0.6
        cb_weight = 0.4
        
        combined = {}
        for rec in cf_recs:
            combined[rec['product_id']] = rec['score'] * cf_weight
        
        for rec in cb_recs:
            if rec['product_id'] in combined:
                combined[rec['product_id']] += rec['score'] * cb_weight
            else:
                combined[rec['product_id']] = rec['score'] * cb_weight
        
        return sorted(combined.items(), key=lambda x: x[1], reverse=True)