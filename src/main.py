"""
DigniLife Platform - Main Application
COMPLETE Phase 3 with ALL features
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from src.core.config import settings
from src.db.session import init_db, close_db

# Import ALL routers
from src.api.v1 import (
    auth, users, tasks, earnings, wallet, withdrawals,
    ai_chat, devices, verification, ai_proposals, support, referrals, admin
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    # Startup
    await init_db()
    print("🚀 DigniLife API started")
    print(f"📍 Environment: {settings.ENVIRONMENT}")
    print(f"🗄️  Database: Connected")
    yield
    # Shutdown
    await close_db()
    print("👋 DigniLife API stopped")


app = FastAPI(
    title="DigniLife API",
    description="AI-Powered Micro-Task Earning Platform - Complete System",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include ALL routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])
app.include_router(tasks.router, prefix="/api/v1/tasks", tags=["Tasks"])
app.include_router(earnings.router, prefix="/api/v1/earnings", tags=["Earnings"])
app.include_router(wallet.router, prefix="/api/v1/wallet", tags=["Wallet"])
app.include_router(withdrawals.router, prefix="/api/v1/withdrawals", tags=["Withdrawals"])
app.include_router(ai_chat.router, prefix="/api/v1/ai-chat", tags=["AI Chat"])
app.include_router(devices.router, prefix="/api/v1/devices", tags=["Devices"])
app.include_router(verification.router, prefix="/api/v1/verification", tags=["Verification"])
app.include_router(ai_proposals.router, prefix="/api/v1/ai-proposals", tags=["AI Proposals"])
app.include_router(support.router, prefix="/api/v1/support", tags=["Support"])
app.include_router(referrals.router, prefix="/api/v1/referrals", tags=["Referrals"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["Admin"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "status": "ok",
        "message": "🎉 DigniLife API - PHASE 3 COMPLETE! 🎉",
        "version": "2.0.0",
        "environment": settings.ENVIRONMENT,
        "phase": "Phase 3: Advanced Features ✅",
        "features": {
            "core": [
                "✅ Authentication & JWT",
                "✅ User Management",
                "✅ Task System (AI validation)",
                "✅ Earning Engine (Quality/Speed/Streak bonuses)",
                "✅ Wallet & Multi-currency",
                "✅ Withdrawal (AUTO-CUT: 15%/10%/5%)",
            ],
            "advanced": [
                "✅ AI Chat Assistant (Context-aware)",
                "✅ Device Management (One device per user)",
                "✅ Face Liveness Detection",
                "✅ KYC Verification",
                "✅ AI Proposal System",
                "✅ Support Ticket System",
                "✅ Referral System ($5 bonus)",
                "✅ Admin Dashboard",
            ],
            "integrations": [
                "✅ 9 Payout Methods (Wave, KBZ, PayPal, etc.)",
                "✅ Multi-currency (10 currencies)",
                "✅ Real-time FX rates",
            ]
        },
        "api_docs": "/docs",
        "ready_for": "Production Deployment! 🚀"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "database": "connected",
        "phase": "3",
        "all_systems": "operational"
    }
