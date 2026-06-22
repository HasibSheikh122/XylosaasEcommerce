# apps/ai_engine/forecasting/prophet_model.py
import pandas as pd
import numpy as np
from prophet import Prophet
from datetime import timedelta

class DemandForecastModel:
    def __init__(self, tenant_id, product_id):
        self.tenant_id = tenant_id
        self.product_id = product_id
        self.model = None
    
    def train(self, historical_data):
        """Train Prophet model on historical sales data"""
        # Prepare data for Prophet
        df = pd.DataFrame(historical_data)
        df = df.rename(columns={'date': 'ds', 'quantity': 'y'})
        
        self.model = Prophet(
            yearly_seasonality=True,
            weekly_seasonality=True,
            daily_seasonality=False,
            changepoint_prior_scale=0.05,
            seasonality_prior_scale=10
        )
        
        # Add additional regressors
        if 'promotion' in df.columns:
            self.model.add_regressor('promotion')
        if 'holiday' in df.columns:
            self.model.add_regressor('holiday')
        
        self.model.fit(df)
        
    def forecast(self, days=30):
        """Generate demand forecast for next N days"""
        future = self.model.make_future_dataframe(periods=days)
        forecast = self.model.predict(future)
        
        return {
            'forecast_dates': forecast['ds'].tail(days).tolist(),
            'predictions': forecast['yhat'].tail(days).tolist(),
            'lower_bound': forecast['yhat_lower'].tail(days).tolist(),
            'upper_bound': forecast['yhat_upper'].tail(days).tolist()
        }