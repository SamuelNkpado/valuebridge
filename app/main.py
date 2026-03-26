from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
import app.models.user
import app.models.business
import app.models.valuation
import app.models.marketplace
import app.models.deal_room
from app.routers import auth, business, valuation, marketplace, reporting, admin, deal_room

app = FastAPI(
    title="ValueBridge API",
    description="Business Valuation & Marketplace Platform for Nigerian SMEs",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)

app.include_router(auth.router)
app.include_router(business.router)
app.include_router(valuation.router)
app.include_router(marketplace.router)
app.include_router(reporting.router)
app.include_router(admin.router)
app.include_router(deal_room.router)

@app.get("/")
def root():
    return {"message": "Welcome to ValueBridge API", "status": "running"}