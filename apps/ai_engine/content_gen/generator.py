# apps/ai_engine/content_gen/generator.py
import random
import string
from transformers import pipeline

class ContentGenerator:
    def __init__(self, tenant_id):
        self.tenant_id = tenant_id
        self.generator = pipeline(
            'text-generation',
            model='gpt2',
            max_length=200
        )
    
    def generate_product_description(self, product_data):
        """Generate product description using AI"""
        
        # Create prompt
        prompt = f"""
        Product: {product_data['name']}
        Category: {product_data.get('category', 'General')}
        Key Features: {', '.join(product_data.get('features', []))}
        Target Audience: {product_data.get('target_audience', 'General consumers')}
        
        Write a compelling product description that highlights benefits and features:
        """
        
        # Generate description
        generated = self.generator(
            prompt,
            max_length=200,
            temperature=0.7,
            top_p=0.9,
            do_sample=True
        )
        
        description = generated[0]['generated_text'].replace(prompt, '').strip()
        
        return {
            'description': description,
            'word_count': len(description.split()),
            'readability': self._calculate_readability(description)
        }
    
    def generate_seo_content(self, product_data):
        """Generate SEO-optimized content"""
        
        seo_data = {
            'meta_title': self._generate_meta_title(product_data),
            'meta_description': self._generate_meta_description(product_data),
            'focus_keywords': self._suggest_keywords(product_data),
            'seo_score': 0  # Will be calculated
        }
        
        seo_data['seo_score'] = self._calculate_seo_score(seo_data)
        
        return seo_data
    
    def _generate_meta_title(self, product_data):
        """Generate SEO meta title"""
        title = f"{product_data['name']} - Buy Online at Best Prices"
        if product_data.get('category'):
            title += f" | {product_data['category']}"
        return title[:70]  # Limit to 70 characters
    
    def _generate_meta_description(self, product_data):
        """Generate SEO meta description"""
        description = f"Shop {product_data['name']} online. "
        if product_data.get('features'):
            description += f"Features: {', '.join(product_data['features'][:3])}. "
        description += f"Best prices. Fast shipping. Buy now!"
        return description[:160]  # Limit to 160 characters