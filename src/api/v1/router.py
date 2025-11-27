from fastapi import APIRouter

# Import endpoint routers (to be created)
# from src.api.v1.endpoints import auth, companies, valuations, forecasts, exports

api_router = APIRouter()

# Health check endpoint
@api_router.get("/health")
async def health():
    return {"status": "healthy", "version": "1.0.0"}

# Include endpoint routers
# api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
# api_router.include_router(companies.router, prefix="/companies", tags=["Companies"])
# api_router.include_router(valuations.router, prefix="/valuations", tags=["Valuations"])
# api_router.include_router(forecasts.router, prefix="/forecasts", tags=["Forecasts"])
# api_router.include_router(exports.router, prefix="/exports", tags=["Exports"])
