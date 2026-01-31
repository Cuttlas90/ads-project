from fastapi import APIRouter

from app.api.routes import (
    auth,
    campaign_applications,
    campaigns,
    channel_managers,
    channels,
    deals,
    health,
    listings,
    marketplace,
)

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(channels.router)
api_router.include_router(channel_managers.router)
api_router.include_router(listings.router)
api_router.include_router(campaigns.router)
api_router.include_router(campaign_applications.router)
api_router.include_router(deals.router)
api_router.include_router(marketplace.router)
api_router.include_router(health.router)
