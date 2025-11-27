"""
Forecast API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from uuid import UUID
import uuid
from decimal import Decimal
from datetime import datetime

from src.core.database import get_db
from src.schemas.forecast import (
    ForecastCreateRequest,
    ForecastResponse,
    ForecastListItem,
    PredictionDataPoint,
    ModelMetrics,
    DataQuality,
    ForecastMethodEnum,
    ScenarioEnum,
)
from src.models.forecast import Forecast, ForecastPrediction
from src.models.user import User
from src.services.forecast import (
    ProphetForecastService,
    ProphetForecastParams,
    ARIMAForecastService,
    ARIMAForecastParams,
    ManualForecastService,
    ManualForecastParams,
)

router = APIRouter(prefix="/forecasts", tags=["forecasts"])


def calculate_forecast(method: str, historical_data: list, years: int, confidence_level: Decimal, model_parameters: dict) -> dict:
    """
    Calculate forecast using specified method.
    
    Args:
        method: Forecast method name
        historical_data: Historical data points
        years: Number of years to forecast
        confidence_level: Confidence level for intervals
        model_parameters: Method-specific parameters
        
    Returns:
        Forecast result dictionary
    """
    if method == ForecastMethodEnum.PROPHET:
        params = ProphetForecastParams(
            historical_data=historical_data,
            years=years,
            confidence_level=confidence_level,
            changepoint_prior_scale=Decimal(str(model_parameters.get("changepoint_prior_scale", 0.05))),
            seasonality_mode=model_parameters.get("seasonality_mode", "additive"),
            yearly_seasonality=model_parameters.get("yearly_seasonality", True),
        )
        result = ProphetForecastService.calculate(params)
        
        # Generate scenarios if requested
        if model_parameters.get("generate_scenarios", True):
            scenarios = ProphetForecastService.generate_scenarios(result['predictions'])
            result['scenarios'] = scenarios
        
        return result
    
    elif method == ForecastMethodEnum.ARIMA:
        params = ARIMAForecastParams(
            historical_data=historical_data,
            years=years,
            confidence_level=confidence_level,
            auto_order=model_parameters.get("auto_order", True),
            order=model_parameters.get("order"),
        )
        result = ARIMAForecastService.calculate(params)
        
        # Generate scenarios if requested
        if model_parameters.get("generate_scenarios", True):
            scenarios = ARIMAForecastService.generate_scenarios(result['predictions'])
            result['scenarios'] = scenarios
        
        return result
    
    elif method == ForecastMethodEnum.MANUAL:
        # For manual forecasts, historical_data contains the projections
        params = ManualForecastParams(
            projections=model_parameters.get("projections", []),
            historical_data=historical_data,
        )
        result = ManualForecastService.calculate(params)
        
        # Generate scenarios if requested
        if model_parameters.get("generate_scenarios", True):
            scenarios = ManualForecastService.generate_scenarios(result['predictions'])
            result['scenarios'] = scenarios
        
        return result
    
    else:
        raise ValueError(f"Unknown forecast method: {method}")


@router.post("", response_model=ForecastResponse, status_code=status.HTTP_201_CREATED)
async def create_forecast(
    request: ForecastCreateRequest,
    db: AsyncSession = Depends(get_db),
    # current_user: User = Depends(get_current_user),  # TODO: Implement authentication
):
    """
    Create a new forecast.
    
    Generates time series forecast using specified method and stores results.
    """
    # Prepare historical data
    historical_data = [
        {"year": point.year, "value": float(point.value)}
        for point in request.historical_data
    ]
    
    # Calculate forecast
    try:
        result = calculate_forecast(
            method=request.method,
            historical_data=historical_data,
            years=request.years,
            confidence_level=request.confidence_level,
            model_parameters={
                **request.model_parameters,
                "generate_scenarios": request.generate_scenarios,
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error calculating forecast: {str(e)}"
        )
    
    # Create forecast in database
    forecast = Forecast(
        id=uuid.uuid4(),
        company_id=UUID(request.company_id),
        created_by=uuid.uuid4(),  # TODO: Use current_user.id
        forecast_type=request.forecast_type,
        method=request.method,
        years=request.years,
        confidence_level=request.confidence_level,
        model_parameters=result['model_parameters'],
        model_metrics=result['model_metrics'],
        data_quality=result['data_quality'],
        validation=result.get('validation'),
        status="completed",
    )
    
    db.add(forecast)
    
    # Create prediction records
    predictions_list = []
    
    # Base case predictions
    for pred in result['predictions']:
        prediction = ForecastPrediction(
            id=uuid.uuid4(),
            forecast_id=forecast.id,
            year=pred['year'],
            predicted_value=Decimal(str(pred['predicted_value'])),
            lower_bound=Decimal(str(pred['lower_bound'])),
            upper_bound=Decimal(str(pred['upper_bound'])),
            scenario=ScenarioEnum.BASE,
        )
        db.add(prediction)
        predictions_list.append(pred)
    
    # Scenario predictions (if generated)
    if 'scenarios' in result and result['scenarios']:
        for scenario_name, scenario_preds in result['scenarios'].items():
            if scenario_name == 'base':
                continue  # Already added
            
            for pred in scenario_preds:
                prediction = ForecastPrediction(
                    id=uuid.uuid4(),
                    forecast_id=forecast.id,
                    year=pred['year'],
                    predicted_value=Decimal(str(pred['predicted_value'])),
                    lower_bound=Decimal(str(pred['lower_bound'])),
                    upper_bound=Decimal(str(pred['upper_bound'])),
                    scenario=ScenarioEnum(scenario_name),
                )
                db.add(prediction)
    
    await db.commit()
    await db.refresh(forecast)
    
    # Prepare response
    predictions_response = [
        PredictionDataPoint(
            year=p['year'],
            predicted_value=p['predicted_value'],
            lower_bound=p['lower_bound'],
            upper_bound=p['upper_bound'],
            scenario=ScenarioEnum.BASE,
            trend=p.get('trend'),
            seasonal=p.get('seasonal'),
        )
        for p in result['predictions']
    ]
    
    # Prepare scenarios response
    scenarios_response = None
    if 'scenarios' in result and result['scenarios']:
        scenarios_response = {}
        for scenario_name, scenario_preds in result['scenarios'].items():
            scenarios_response[scenario_name] = [
                PredictionDataPoint(
                    year=p['year'],
                    predicted_value=p['predicted_value'],
                    lower_bound=p['lower_bound'],
                    upper_bound=p['upper_bound'],
                    scenario=ScenarioEnum(p.get('scenario', scenario_name)),
                )
                for p in scenario_preds
            ]
    
    return ForecastResponse(
        id=str(forecast.id),
        company_id=str(forecast.company_id),
        forecast_type=forecast.forecast_type,
        method=forecast.method,
        years=forecast.years,
        confidence_level=float(forecast.confidence_level),
        predictions=predictions_response,
        scenarios=scenarios_response,
        model_parameters=forecast.model_parameters,
        model_metrics=ModelMetrics(**forecast.model_metrics),
        data_quality=DataQuality(**forecast.data_quality),
        validation=forecast.validation,
        created_at=forecast.created_at.isoformat(),
        updated_at=forecast.updated_at.isoformat(),
    )


@router.get("/{forecast_id}", response_model=ForecastResponse)
async def get_forecast(
    forecast_id: UUID,
    db: AsyncSession = Depends(get_db),
    # current_user: User = Depends(get_current_user),
):
    """
    Get a forecast by ID.
    """
    from sqlalchemy import select
    
    result = await db.execute(
        select(Forecast).where(Forecast.id == forecast_id)
    )
    forecast = result.scalar_one_or_none()
    
    if not forecast:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Forecast not found"
        )
    
    # Get predictions
    result = await db.execute(
        select(ForecastPrediction).where(
            ForecastPrediction.forecast_id == forecast_id
        ).order_by(ForecastPrediction.year)
    )
    predictions_models = result.scalars().all()
    
    # Separate by scenario
    base_predictions = []
    scenarios = {'base': [], 'best': [], 'worst': []}
    
    for pm in predictions_models:
        pred_data = PredictionDataPoint(
            year=pm.year,
            predicted_value=float(pm.predicted_value),
            lower_bound=float(pm.lower_bound),
            upper_bound=float(pm.upper_bound),
            scenario=pm.scenario,
        )
        
        if pm.scenario == ScenarioEnum.BASE:
            base_predictions.append(pred_data)
        
        scenarios[pm.scenario].append(pred_data)
    
    return ForecastResponse(
        id=str(forecast.id),
        company_id=str(forecast.company_id),
        forecast_type=forecast.forecast_type,
        method=forecast.method,
        years=forecast.years,
        confidence_level=float(forecast.confidence_level),
        predictions=base_predictions,
        scenarios=scenarios if len(scenarios['best']) > 0 else None,
        model_parameters=forecast.model_parameters,
        model_metrics=ModelMetrics(**forecast.model_metrics),
        data_quality=DataQuality(**forecast.data_quality),
        validation=forecast.validation,
        created_at=forecast.created_at.isoformat(),
        updated_at=forecast.updated_at.isoformat(),
    )


@router.get("", response_model=List[ForecastListItem])
async def list_forecasts(
    company_id: UUID = None,
    forecast_type: str = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    # current_user: User = Depends(get_current_user),
):
    """
    List forecasts with optional filtering.
    """
    from sqlalchemy import select
    
    query = select(Forecast)
    
    if company_id:
        query = query.where(Forecast.company_id == company_id)
    
    if forecast_type:
        query = query.where(Forecast.forecast_type == forecast_type)
    
    query = query.offset(skip).limit(limit).order_by(Forecast.created_at.desc())
    
    result = await db.execute(query)
    forecasts = result.scalars().all()
    
    return [
        ForecastListItem(
            id=str(f.id),
            company_id=str(f.company_id),
            forecast_type=f.forecast_type,
            method=f.method,
            years=f.years,
            status=f.status,
            created_at=f.created_at.isoformat(),
        )
        for f in forecasts
    ]


@router.delete("/{forecast_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_forecast(
    forecast_id: UUID,
    db: AsyncSession = Depends(get_db),
    # current_user: User = Depends(get_current_user),
):
    """
    Delete a forecast.
    """
    from sqlalchemy import select, delete
    
    result = await db.execute(
        select(Forecast).where(Forecast.id == forecast_id)
    )
    forecast = result.scalar_one_or_none()
    
    if not forecast:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Forecast not found"
        )
    
    # Delete predictions first (cascade should handle this, but explicit is better)
    await db.execute(
        delete(ForecastPrediction).where(ForecastPrediction.forecast_id == forecast_id)
    )
    
    # Delete forecast
    await db.delete(forecast)
    await db.commit()
    
    return None
