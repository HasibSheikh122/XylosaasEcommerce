# apps/ai_engine/churn/predictor.py
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score

class ChurnPredictor:
    def __init__(self, tenant_id):
        self.tenant_id = tenant_id
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42
        )
        self.feature_columns = []
    
    def train(self, historical_data):
        """Train churn prediction model"""
        
        # Prepare training data
        df = pd.DataFrame(historical_data)
        
        # Feature engineering
        df['avg_order_value'] = df['total_spent'] / (df['order_count'] + 1)
        df['days_since_last_order'] = (pd.Timestamp.now() - pd.to_datetime(df['last_order_date'])).dt.days
        df['purchase_frequency'] = df['order_count'] / df['customer_lifetime_days'].clip(lower=1)
        
        # Define features
        self.feature_columns = [
            'days_since_last_order',
            'order_count',
            'total_spent',
            'avg_order_value',
            'purchase_frequency',
            'customer_lifetime_days'
        ]
        
        X = df[self.feature_columns]
        y = df['churned']
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Train model
        self.model.fit(X_train, y_train)
        
        # Evaluate
        y_pred = self.model.predict(X_test)
        
        return {
            'accuracy': accuracy_score(y_test, y_pred),
            'precision': precision_score(y_test, y_pred, average='weighted'),
            'recall': recall_score(y_test, y_pred, average='weighted'),
            'feature_importance': dict(zip(
                self.feature_columns,
                self.model.feature_importances_
            ))
        }
    
    def predict_churn(self, customer_data):
        """Predict churn risk for a customer"""
        
        # Prepare features
        features = np.array([[
            customer_data.get('days_since_last_order', 30),
            customer_data.get('order_count', 0),
            customer_data.get('total_spent', 0),
            customer_data.get('avg_order_value', 0),
            customer_data.get('purchase_frequency', 0),
            customer_data.get('customer_lifetime_days', 1)
        ]])
        
        # Predict
        churn_probability = self.model.predict_proba(features)[0][1]
        
        # Determine churn risk level
        if churn_probability > 0.7:
            risk_level = 'high'
        elif churn_probability > 0.4:
            risk_level = 'medium'
        else:
            risk_level = 'low'
        
        return {
            'churn_probability': churn_probability,
            'risk_level': risk_level,
            'factors': self._get_risk_factors(customer_data)
        }
    
    def _get_risk_factors(self, customer_data):
        """Identify churn risk factors"""
        factors = []
        
        if customer_data.get('days_since_last_order', 30) > 60:
            factors.append('inactivity')
        if customer_data.get('order_count', 0) < 3:
            factors.append('low_engagement')
        if customer_data.get('avg_order_value', 0) < 50:
            factors.append('low_value')
        
        return factors