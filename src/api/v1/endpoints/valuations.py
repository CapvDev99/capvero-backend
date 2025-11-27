"""
Valuation API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from uuid import UUID
import uuid
from decimal import Decimal
from datetime import datetime

from src.core.database import get_db
from src.schemas.valuation import (
    ValuationCreateRequest,
    ValuationResponse,
    ValuationMethodResult,
    SensitivityAnalysisRequest,
    SensitivityAnalysisResponse,
    ValuationMethodEnum,
)
from src.models.valuation import Valuation, ValuationMethodResult as ValuationMethodResultModel, SensitivityAnalysis
from src.models.user import User
from src.services.valuation import (
    EBITDAMultipleService,
    EBITDAMultipleParams,
    CompanySize,
    DCFService,
    DCFParams,
    EarningsValueService,
    EarningsValueParams,
    AssetValueService,
    AssetValueParams,
    PractitionerService,
    PractitionerParams,
    SensitivityService,
    SensitivityParams,
)

router = APIRouter(prefix="/valuations", tags=["valuations"])


def calculate_valuation_method(method: str, parameters: dict) -> dict:
    """
    Calculate valuation using specified method and parameters.
    
    Args:
        method: Valuation method name
        parameters: Method-specific parameters
        
    Returns:
        Valuation result dictionary
    """
    if method == ValuationMethodEnum.EBITDA_MULTIPLE:
        params = EBITDAMultipleParams(
            ebitda=Decimal(str(parameters["ebitda"])),
            base_multiple=Decimal(str(parameters["base_multiple"])),
            growth_rate=Decimal(str(parameters["growth_rate"])),
            risk_score=int(parameters["risk_score"]),
            company_size=CompanySize(parameters["company_size"]),
            cash=Decimal(str(parameters.get("cash", 0))),
            debt=Decimal(str(parameters.get("debt", 0))),
            non_operating_assets=Decimal(str(parameters.get("non_operating_assets", 0))),
        )
        return EBITDAMultipleService.calculate(params)
    
    elif method == ValuationMethodEnum.DCF:
        params = DCFParams(
            fcf_projections=[Decimal(str(fcf)) for fcf in parameters["fcf_projections"]],
            wacc=Decimal(str(parameters["wacc"])) / Decimal("100"),  # Convert percentage to decimal
            terminal_growth_rate=Decimal(str(parameters["terminal_growth_rate"])) / Decimal("100"),
            cash=Decimal(str(parameters.get("cash", 0))),
            debt=Decimal(str(parameters.get("debt", 0))),
            non_operating_assets=Decimal(str(parameters.get("non_operating_assets", 0))),
        )
        return DCFService.calculate(params)
    
    elif method == ValuationMethodEnum.EARNINGS_VALUE:
        params = EarningsValueParams(
            historical_earnings=[Decimal(str(e)) for e in parameters["historical_earnings"]],
            risk_free_rate=Decimal(str(parameters["risk_free_rate"])) / Decimal("100"),
            risk_premium=Decimal(str(parameters["risk_premium"])) / Decimal("100"),
            use_practitioner_method=parameters.get("use_practitioner_method", False),
            asset_value=Decimal(str(parameters["asset_value"])) if parameters.get("asset_value") else None,
        )
        return EarningsValueService.calculate(params)
    
    elif method == ValuationMethodEnum.ASSET_VALUE:
        params = AssetValueParams(
            real_estate_market_value=Decimal(str(parameters["real_estate_market_value"])),
            machinery_replacement_value=Decimal(str(parameters["machinery_replacement_value"])),
            machinery_depreciation=Decimal(str(parameters["machinery_depreciation"])),
            inventory_value=Decimal(str(parameters["inventory_value"])),
            receivables=Decimal(str(parameters["receivables"])),
            receivables_risk=Decimal(str(parameters["receivables_risk"])),
            cash=Decimal(str(parameters["cash"])),
            intangible_assets=Decimal(str(parameters["intangible_assets"])),
            liabilities=Decimal(str(parameters["liabilities"])),
        )
        return AssetValueService.calculate(params)
    
    elif method == ValuationMethodEnum.PRACTITIONER:
        params = PractitionerParams(
            earnings_value=Decimal(str(parameters["earnings_value"])),
            asset_value=Decimal(str(parameters["asset_value"])),
            earnings_weight=Decimal(str(parameters.get("earnings_weight", 0.67))),
        )
        return PractitionerService.calculate(params)
    
    else:
        raise ValueError(f"Unknown valuation method: {method}")


@router.post("", response_model=ValuationResponse, status_code=status.HTTP_201_CREATED)
async def create_valuation(
    request: ValuationCreateRequest,
    db: AsyncSession = Depends(get_db),
    # current_user: User = Depends(get_current_user),  # TODO: Implement authentication
):
    """
    Create a new valuation.
    
    Calculates company value using specified methods and stores results.
    """
    # Calculate all methods
    method_results = []
    total_weight = Decimal("0")
    
    for method_request in request.methods:
        try:
            result = calculate_valuation_method(
                method_request.method,
                method_request.parameters
            )
            
            method_results.append({
                "method": method_request.method,
                "calculated_value": result["calculated_value"],
                "enterprise_value": result.get("enterprise_value"),
                "equity_value": result.get("equity_value", result["calculated_value"]),
                "weight": float(method_request.weight),
                "details": result["details"],
            })
            
            total_weight += method_request.weight
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error calculating {method_request.method}: {str(e)}"
            )
    
    # Normalize weights
    if total_weight > 0:
        for result in method_results:
            result["weight"] = result["weight"] / float(total_weight)
    
    # Calculate weighted final value
    final_value = sum(
        Decimal(str(r["calculated_value"])) * Decimal(str(r["weight"]))
        for r in method_results
    )
    
    # Calculate value range (±15% as example)
    final_value_min = final_value * Decimal("0.85")
    final_value_max = final_value * Decimal("1.15")
    
    # Create valuation in database
    valuation = Valuation(
        id=uuid.uuid4(),
        company_id=UUID(request.company_id),
        created_by=uuid.uuid4(),  # TODO: Use current_user.id
        name=request.name,
        valuation_date=request.valuation_date,
        assumptions=request.assumptions,
        status="completed",
        final_value=final_value,
        final_value_min=final_value_min,
        final_value_max=final_value_max,
        currency=request.currency,
    )
    
    db.add(valuation)
    
    # Create method results in database
    for result in method_results:
        method_result_model = ValuationMethodResultModel(
            id=uuid.uuid4(),
            valuation_id=valuation.id,
            method=result["method"],
            parameters=request.methods[method_results.index(result)].parameters,
            calculated_value=Decimal(str(result["calculated_value"])),
            weight=Decimal(str(result["weight"])),
            details=result["details"],
        )
        db.add(method_result_model)
    
    await db.commit()
    await db.refresh(valuation)
    
    # Return response
    return ValuationResponse(
        id=str(valuation.id),
        company_id=str(valuation.company_id),
        name=valuation.name,
        valuation_date=valuation.valuation_date,
        status=valuation.status,
        final_value=float(valuation.final_value),
        final_value_min=float(valuation.final_value_min),
        final_value_max=float(valuation.final_value_max),
        currency=valuation.currency,
        method_results=method_results,
        assumptions=valuation.assumptions,
        created_at=valuation.created_at.isoformat(),
        updated_at=valuation.updated_at.isoformat(),
    )


@router.get("/{valuation_id}", response_model=ValuationResponse)
async def get_valuation(
    valuation_id: UUID,
    db: AsyncSession = Depends(get_db),
    # current_user: User = Depends(get_current_user),
):
    """
    Get a valuation by ID.
    """
    from sqlalchemy import select
    
    result = await db.execute(
        select(Valuation).where(Valuation.id == valuation_id)
    )
    valuation = result.scalar_one_or_none()
    
    if not valuation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Valuation not found"
        )
    
    # Get method results
    result = await db.execute(
        select(ValuationMethodResultModel).where(
            ValuationMethodResultModel.valuation_id == valuation_id
        )
    )
    method_results_models = result.scalars().all()
    
    method_results = [
        {
            "method": mr.method,
            "calculated_value": float(mr.calculated_value),
            "enterprise_value": None,  # TODO: Store in details
            "equity_value": float(mr.calculated_value),
            "weight": float(mr.weight),
            "details": mr.details,
        }
        for mr in method_results_models
    ]
    
    return ValuationResponse(
        id=str(valuation.id),
        company_id=str(valuation.company_id),
        name=valuation.name,
        valuation_date=valuation.valuation_date,
        status=valuation.status,
        final_value=float(valuation.final_value) if valuation.final_value else None,
        final_value_min=float(valuation.final_value_min) if valuation.final_value_min else None,
        final_value_max=float(valuation.final_value_max) if valuation.final_value_max else None,
        currency=valuation.currency,
        method_results=method_results,
        assumptions=valuation.assumptions,
        created_at=valuation.created_at.isoformat(),
        updated_at=valuation.updated_at.isoformat(),
    )


@router.post("/{valuation_id}/sensitivity", response_model=SensitivityAnalysisResponse)
async def create_sensitivity_analysis(
    valuation_id: UUID,
    request: SensitivityAnalysisRequest,
    db: AsyncSession = Depends(get_db),
    # current_user: User = Depends(get_current_user),
):
    """
    Perform sensitivity analysis on a valuation.
    """
    # TODO: Implement sensitivity analysis
    # This would retrieve the valuation, run sensitivity analysis using SensitivityService,
    # and store the results
    
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Sensitivity analysis not yet implemented"
    )


@router.get("", response_model=List[ValuationResponse])
async def list_valuations(
    company_id: UUID = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    # current_user: User = Depends(get_current_user),
):
    """
    List valuations with optional filtering.
    """
    from sqlalchemy import select
    
    query = select(Valuation)
    
    if company_id:
        query = query.where(Valuation.company_id == company_id)
    
    query = query.offset(skip).limit(limit).order_by(Valuation.created_at.desc())
    
    result = await db.execute(query)
    valuations = result.scalars().all()
    
    # Convert to response format
    response = []
    for valuation in valuations:
        response.append(
            ValuationResponse(
                id=str(valuation.id),
                company_id=str(valuation.company_id),
                name=valuation.name,
                valuation_date=valuation.valuation_date,
                status=valuation.status,
                final_value=float(valuation.final_value) if valuation.final_value else None,
                final_value_min=float(valuation.final_value_min) if valuation.final_value_min else None,
                final_value_max=float(valuation.final_value_max) if valuation.final_value_max else None,
                currency=valuation.currency,
                method_results=[],  # Empty for list view
                assumptions=valuation.assumptions,
                created_at=valuation.created_at.isoformat(),
                updated_at=valuation.updated_at.isoformat(),
            )
        )
    
    return response
