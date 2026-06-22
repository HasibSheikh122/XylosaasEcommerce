# apps/ai_engine/fraud/detector.py
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

class FraudDetector:
    def __init__(self, tenant_id):
        self.tenant_id = tenant_id
        self.model = IsolationForest(
            contamination=0.1,
            random_state=42
        )
        self.scaler = StandardScaler()
    
    def detect_fraud(self, order_data):
        """Detect potential fraud in an order"""
        
        # Extract features
        features = self._extract_features(order_data)
        
        # Scale features
        scaled_features = self.scaler.transform([features])
        
        # Predict anomaly
        anomaly_score = self.model.decision_function(scaled_features)[0]
        is_anomaly = self.model.predict(scaled_features)[0] == -1
        
        # Calculate risk score (0-100)
        risk_score = min(100, max(0, (1 - anomaly_score) * 50))
        
        # Risk factors
        risk_factors = self._identify_risk_factors(order_data)
        
        return {
            'risk_score': risk_score,
            'risk_level': self._get_risk_level(risk_score),
            'is_fraudulent': is_anomaly and risk_score > 70,
            'risk_factors': risk_factors,
            'recommendations': self._get_recommendations(risk_score, risk_factors)
        }
    
    def _extract_features(self, order_data):
        """Extract features for fraud detection"""
        features = []
        
        # Order characteristics
        features.append(order_data.get('order_amount', 0))
        features.append(order_data.get('items_count', 1))
        
        # Customer characteristics
        customer_data = order_data.get('customer', {})
        features.append(customer_data.get('order_count', 0))
        features.append(customer_data.get('days_since_first_order', 1))
        
        # Location characteristics
        features.append(self._calculate_distance_score(
            order_data.get('shipping_address', {})
        ))
        
        # Device characteristics
        features.append(self._calculate_device_score(
            order_data.get('user_agent', '')
        ))
        
        # Time characteristics
        features.append(self._calculate_time_score(
            order_data.get('created_at', None)
        ))
        
        return np.array(features)
    
    def _identify_risk_factors(self, order_data):
        """Identify specific risk factors"""
        risk_factors = []
        
        if order_data.get('order_amount', 0) > 10000:
            risk_factors.append('high_order_value')
        
        if order_data.get('shipping_address', {}).get('is_po_box', False):
            risk_factors.append('po_box_address')
        
        if order_data.get('billing_address') != order_data.get('shipping_address'):
            risk_factors.append('address_mismatch')
        
        if order_data.get('ip_address', ''):
            # Check if IP is high-risk
            risk_factors.append('high_risk_ip')
        
        return risk_factors