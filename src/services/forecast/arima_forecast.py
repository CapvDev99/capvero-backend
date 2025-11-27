"""
ARIMA Forecast Service

Implements time series forecasting using ARIMA models.
"""

from typing import List, Dict, Any, Tuple
from decimal import Decimal
import numpy as np
import pandas as pd


class ARIMAForecastParams:
    """Parameters for ARIMA forecasting."""
    
    def __init__(
        self,
        historical_data: List[Dict[str, Any]],
        years: int,
        confidence_level: Decimal = Decimal("0.95"),
        auto_order: bool = True,
        order: Tuple[int, int, int] = None,
    ):
        self.historical_data = historical_data
        self.years = years
        self.confidence_level = confidence_level
        self.auto_order = auto_order
        self.order = order
        
        # Validation
        if not historical_data:
            raise ValueError("Historical data cannot be empty")
        if len(historical_data) < 3:
            raise ValueError("At least 3 years of historical data required for ARIMA")
        if years < 1 or years > 10:
            raise ValueError("Forecast years must be between 1 and 10")
        if confidence_level <= 0 or confidence_level >= 1:
            raise ValueError("Confidence level must be between 0 and 1")
        if not auto_order and order is None:
            raise ValueError("Order must be specified when auto_order is False")


class ARIMAForecastService:
    """Service for ARIMA-based forecasting."""
    
    @staticmethod
    def prepare_data(historical_data: List[Dict[str, Any]]) -> np.ndarray:
        """
        Prepare historical data for ARIMA.
        
        Args:
            historical_data: List of dicts with 'year' and 'value' keys
            
        Returns:
            NumPy array of values
        """
        df = pd.DataFrame(historical_data)
        return df['value'].astype(float).values
    
    @staticmethod
    def check_stationarity(data: np.ndarray) -> Dict[str, Any]:
        """
        Check if time series is stationary using Augmented Dickey-Fuller test.
        
        Args:
            data: Time series data
            
        Returns:
            Dictionary with test results
        """
        try:
            from statsmodels.tsa.stattools import adfuller
        except ImportError:
            raise ImportError(
                "statsmodels is not installed. Install with: pip install statsmodels"
            )
        
        result = adfuller(data)
        
        return {
            'is_stationary': result[1] < 0.05,  # p-value < 0.05
            'adf_statistic': float(result[0]),
            'p_value': float(result[1]),
            'critical_values': {k: float(v) for k, v in result[4].items()},
        }
    
    @staticmethod
    def auto_select_order(data: np.ndarray, max_p: int = 3, max_q: int = 3) -> Tuple[int, int, int]:
        """
        Automatically select best ARIMA order using AIC criterion.
        
        Args:
            data: Time series data
            max_p: Maximum AR order to test
            max_q: Maximum MA order to test
            
        Returns:
            Tuple (p, d, q) representing best ARIMA order
        """
        try:
            from statsmodels.tsa.arima.model import ARIMA
        except ImportError:
            raise ImportError(
                "statsmodels is not installed. Install with: pip install statsmodels"
            )
        
        # Check stationarity to determine d
        stationarity = ARIMAForecastService.check_stationarity(data)
        d = 0 if stationarity['is_stationary'] else 1
        
        best_aic = np.inf
        best_order = (1, d, 1)
        
        for p in range(0, max_p + 1):
            for q in range(0, max_q + 1):
                try:
                    model = ARIMA(data, order=(p, d, q))
                    fitted = model.fit()
                    
                    if fitted.aic < best_aic:
                        best_aic = fitted.aic
                        best_order = (p, d, q)
                except:
                    # Skip if model doesn't converge
                    continue
        
        return best_order
    
    @classmethod
    def calculate(cls, params: ARIMAForecastParams) -> Dict[str, Any]:
        """
        Generate forecast using ARIMA.
        
        Args:
            params: Forecast parameters
            
        Returns:
            Dictionary with forecast results
        """
        try:
            from statsmodels.tsa.arima.model import ARIMA
        except ImportError:
            raise ImportError(
                "statsmodels is not installed. Install with: pip install statsmodels"
            )
        
        # Step 1: Prepare data
        values = cls.prepare_data(params.historical_data)
        
        # Step 2: Check stationarity
        stationarity_test = cls.check_stationarity(values)
        
        # Step 3: Determine ARIMA order
        if params.auto_order:
            order = cls.auto_select_order(values)
        else:
            order = params.order
        
        # Step 4: Fit ARIMA model
        model = ARIMA(values, order=order)
        fitted_model = model.fit()
        
        # Step 5: Generate forecast
        alpha = 1 - float(params.confidence_level)
        forecast_result = fitted_model.get_forecast(steps=params.years, alpha=alpha)
        
        # Step 6: Extract predictions
        forecast_values = forecast_result.predicted_mean
        conf_int = forecast_result.conf_int(alpha=alpha)
        
        predictions = []
        base_year = params.historical_data[-1]['year']
        
        for i in range(params.years):
            predictions.append({
                'year': base_year + i + 1,
                'predicted_value': float(forecast_values.iloc[i]),
                'lower_bound': float(conf_int.iloc[i, 0]),
                'upper_bound': float(conf_int.iloc[i, 1]),
            })
        
        # Step 7: Calculate model metrics (on historical data)
        fitted_values = fitted_model.fittedvalues
        
        # Align actual and fitted values (ARIMA may drop first few observations)
        actual = values[-len(fitted_values):]
        
        # MAPE (Mean Absolute Percentage Error)
        mape = np.mean(np.abs((actual - fitted_values) / actual)) * 100
        
        # RMSE (Root Mean Square Error)
        rmse = np.sqrt(np.mean((actual - fitted_values) ** 2))
        
        # MAE (Mean Absolute Error)
        mae = np.mean(np.abs(actual - fitted_values))
        
        return {
            'method': 'arima',
            'predictions': predictions,
            'model_parameters': {
                'order': order,
                'p': order[0],
                'd': order[1],
                'q': order[2],
                'aic': float(fitted_model.aic),
                'bic': float(fitted_model.bic),
                'confidence_level': float(params.confidence_level),
            },
            'model_metrics': {
                'mape': float(mape),
                'rmse': float(rmse),
                'mae': float(mae),
            },
            'stationarity_test': stationarity_test,
            'data_quality': {
                'data_points': len(values),
                'missing_values': 0,
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
