"""
Prophet Forecast Service

Implements time series forecasting using Facebook Prophet.
"""

from typing import List, Dict, Any, Optional
from decimal import Decimal
from datetime import datetime, date
import pandas as pd
import numpy as np


class ProphetForecastParams:
    """Parameters for Prophet forecasting."""
    
    def __init__(
        self,
        historical_data: List[Dict[str, Any]],
        years: int,
        confidence_level: Decimal = Decimal("0.95"),
        changepoint_prior_scale: Decimal = Decimal("0.05"),
        seasonality_mode: str = "additive",
        yearly_seasonality: bool = True,
    ):
        self.historical_data = historical_data
        self.years = years
        self.confidence_level = confidence_level
        self.changepoint_prior_scale = changepoint_prior_scale
        self.seasonality_mode = seasonality_mode
        self.yearly_seasonality = yearly_seasonality
        
        # Validation
        if not historical_data:
            raise ValueError("Historical data cannot be empty")
        if len(historical_data) < 3:
            raise ValueError("At least 3 years of historical data required for Prophet")
        if years < 1 or years > 10:
            raise ValueError("Forecast years must be between 1 and 10")
        if confidence_level <= 0 or confidence_level >= 1:
            raise ValueError("Confidence level must be between 0 and 1")


class ProphetForecastService:
    """Service for Prophet-based forecasting."""
    
    @staticmethod
    def prepare_data(historical_data: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Prepare historical data for Prophet.
        
        Prophet requires a DataFrame with columns 'ds' (date) and 'y' (value).
        
        Args:
            historical_data: List of dicts with 'year' and 'value' keys
            
        Returns:
            DataFrame with 'ds' and 'y' columns
        """
        df = pd.DataFrame(historical_data)
        
        # Convert year to datetime (using year-end date)
        df['ds'] = pd.to_datetime(df['year'].astype(str) + '-12-31')
        df['y'] = df['value'].astype(float)
        
        return df[['ds', 'y']]
    
    @staticmethod
    def detect_outliers_iqr(data: pd.Series) -> pd.Series:
        """
        Detect outliers using Interquartile Range (IQR) method.
        
        Args:
            data: Pandas Series of values
            
        Returns:
            Boolean Series indicating outliers
        """
        Q1 = data.quantile(0.25)
        Q3 = data.quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        return (data < lower_bound) | (data > upper_bound)
    
    @classmethod
    def calculate(cls, params: ProphetForecastParams) -> Dict[str, Any]:
        """
        Generate forecast using Prophet.
        
        Args:
            params: Forecast parameters
            
        Returns:
            Dictionary with forecast results
        """
        try:
            from prophet import Prophet
        except ImportError:
            raise ImportError(
                "Prophet is not installed. Install with: pip install prophet"
            )
        
        # Step 1: Prepare data
        df = cls.prepare_data(params.historical_data)
        
        # Step 2: Detect outliers (for information only)
        outliers = cls.detect_outliers_iqr(df['y'])
        outlier_count = outliers.sum()
        
        # Step 3: Initialize Prophet model
        model = Prophet(
            interval_width=float(params.confidence_level),
            changepoint_prior_scale=float(params.changepoint_prior_scale),
            seasonality_mode=params.seasonality_mode,
            yearly_seasonality=params.yearly_seasonality,
            weekly_seasonality=False,
            daily_seasonality=False,
        )
        
        # Step 4: Fit model
        model.fit(df)
        
        # Step 5: Create future dataframe
        future = model.make_future_dataframe(periods=params.years, freq='Y')
        
        # Step 6: Generate forecast
        forecast = model.predict(future)
        
        # Step 7: Extract predictions (only future years)
        predictions = []
        forecast_start_idx = len(df)
        
        for i in range(forecast_start_idx, forecast_start_idx + params.years):
            row = forecast.iloc[i]
            predictions.append({
                'year': row['ds'].year,
                'predicted_value': float(row['yhat']),
                'lower_bound': float(row['yhat_lower']),
                'upper_bound': float(row['yhat_upper']),
                'trend': float(row['trend']),
                'seasonal': float(row.get('yearly', 0)),
            })
        
        # Step 8: Calculate model metrics (on historical data)
        historical_forecast = forecast.iloc[:forecast_start_idx]
        actual = df['y'].values
        predicted = historical_forecast['yhat'].values
        
        # MAPE (Mean Absolute Percentage Error)
        mape = np.mean(np.abs((actual - predicted) / actual)) * 100
        
        # RMSE (Root Mean Square Error)
        rmse = np.sqrt(np.mean((actual - predicted) ** 2))
        
        # MAE (Mean Absolute Error)
        mae = np.mean(np.abs(actual - predicted))
        
        return {
            'method': 'prophet',
            'predictions': predictions,
            'model_parameters': {
                'changepoint_prior_scale': float(params.changepoint_prior_scale),
                'seasonality_mode': params.seasonality_mode,
                'yearly_seasonality': params.yearly_seasonality,
                'confidence_level': float(params.confidence_level),
            },
            'model_metrics': {
                'mape': float(mape),
                'rmse': float(rmse),
                'mae': float(mae),
                'outlier_count': int(outlier_count),
            },
            'data_quality': {
                'data_points': len(df),
                'outliers_detected': int(outlier_count),
                'missing_values': 0,  # Prophet handles missing values
            },
        }
    
    @staticmethod
    def generate_scenarios(
        base_predictions: List[Dict[str, Any]],
        volatility_factor: float = 0.15
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Generate Best/Worst case scenarios based on base predictions.
        
        Args:
            base_predictions: List of base case predictions
            volatility_factor: Factor for scenario spread (default 15%)
            
        Returns:
            Dictionary with 'base', 'best', 'worst' scenarios
        """
        scenarios = {
            'base': base_predictions,
            'best': [],
            'worst': []
        }
        
        for pred in base_predictions:
            # Best Case: Upper bound + additional premium
            best_value = pred['upper_bound'] * (1 + volatility_factor)
            
            # Worst Case: Lower bound - additional discount
            worst_value = pred['lower_bound'] * (1 - volatility_factor)
            
            scenarios['best'].append({
                'year': pred['year'],
                'predicted_value': best_value,
                'lower_bound': pred['lower_bound'],
                'upper_bound': pred['upper_bound'],
                'scenario': 'best',
            })
            
            scenarios['worst'].append({
                'year': pred['year'],
                'predicted_value': worst_value,
                'lower_bound': pred['lower_bound'],
                'upper_bound': pred['upper_bound'],
                'scenario': 'worst',
            })
        
        return scenarios
