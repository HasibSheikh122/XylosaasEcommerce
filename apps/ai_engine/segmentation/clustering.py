# apps/ai_engine/segmentation/clustering.py
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA

class CustomerSegmenter:
    def __init__(self, tenant_id):
        self.tenant_id = tenant_id
        self.scaler = StandardScaler()
        self.kmeans = KMeans(n_clusters=5, random_state=42)
    
    def segment_customers(self, customer_data):
        """Segment customers using RFM analysis and clustering"""
        
        # Feature engineering
        features = self._extract_features(customer_data)
        
        # Scale features
        scaled_features = self.scaler.fit_transform(features)
        
        # Perform clustering
        clusters = self.kmeans.fit_predict(scaled_features)
        
        # Analyze clusters
        segments = []
        for cluster_id in range(self.kmeans.n_clusters):
            cluster_mask = clusters == cluster_id
            cluster_customers = customer_data[cluster_mask]
            
            segment = {
                'id': cluster_id,
                'size': len(cluster_customers),
                'characteristics': self._analyze_cluster(cluster_customers),
                'centroid': self.kmeans.cluster_centers_[cluster_id].tolist()
            }
            segments.append(segment)
        
        return segments
    
    def _extract_features(self, customer_data):
        """Extract features for clustering"""
        features = []
        for customer in customer_data:
            # RFM features
            recency = customer.get('days_since_last_order', 30)
            frequency = customer.get('order_count', 0)
            monetary = customer.get('total_spent', 0)
            
            # Additional features
            avg_order_value = monetary / frequency if frequency > 0 else 0
            lifetime = customer.get('customer_lifetime_days', 1)
            purchase_velocity = frequency / lifetime if lifetime > 0 else 0
            
            features.append([
                recency,
                frequency,
                monetary,
                avg_order_value,
                purchase_velocity
            ])
        
        return np.array(features)
    
    def _analyze_cluster(self, customers):
        """Analyze cluster characteristics"""
        return {
            'avg_recency': np.mean([c.get('days_since_last_order', 30) for c in customers]),
            'avg_frequency': np.mean([c.get('order_count', 0) for c in customers]),
            'avg_monetary': np.mean([c.get('total_spent', 0) for c in customers]),
            'avg_order_value': np.mean([
                c.get('total_spent', 0) / max(c.get('order_count', 1), 1) 
                for c in customers
            ])
        }