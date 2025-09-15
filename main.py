#!/usr/bin/env python3
"""
FastAPI application for FlexTraff traffic management system
Provides REST APIs for traffic calculation and data management
"""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any
from datetime import datetime, date
import logging
import asyncio

from app.services.traffic_calculator import TrafficCalculator
from app.services.database_service import DatabaseService

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="FlexTraff ATCS API",
    description="Adaptive Traffic Control System for intelligent traffic management",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global services
db_service = None
traffic_calculator = None

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    global db_service, traffic_calculator
    logger.info("🚀 Starting FlexTraff ATCS API...")
    
    try:
        db_service = DatabaseService()
        traffic_calculator = TrafficCalculator(db_service=db_service)
        
        # Test database connection
        health = await db_service.health_check()
        if health["database_connected"]:
            logger.info("✅ Database connection established")
        else:
            logger.error(f"❌ Database connection failed: {health.get('error')}")
            
    except Exception as e:
        logger.error(f"❌ Startup failed: {str(e)}")
        raise

# Dependency to get database service
async def get_db_service() -> DatabaseService:
    if db_service is None:
        raise HTTPException(status_code=500, detail="Database service not initialized")
    return db_service

# Dependency to get traffic calculator
async def get_traffic_calculator() -> TrafficCalculator:
    if traffic_calculator is None:
        raise HTTPException(status_code=500, detail="Traffic calculator not initialized")
    return traffic_calculator

# Pydantic models for API requests/responses
class LaneCountsRequest(BaseModel):
    lane_counts: List[int] = Field(..., description="Vehicle counts for each lane [North, South, East, West]", min_length=4, max_length=4)
    junction_id: Optional[int] = Field(None, description="Junction ID for database logging", ge=1)

    @field_validator('lane_counts')
    @classmethod
    def validate_lane_counts(cls, v):
        if len(v) != 4:
            raise ValueError('Exactly 4 lane counts required')
        if any(count < 0 for count in v):
            raise ValueError('Lane counts must be non-negative')
        return v

class TrafficCalculationResponse(BaseModel):
    green_times: List[int] = Field(..., description="Green light durations for each lane")
    cycle_time: int = Field(..., description="Total cycle time in seconds")
    algorithm_info: Dict[str, Any] = Field(..., description="Algorithm execution details")
    junction_id: Optional[int] = Field(None, description="Junction ID if provided")

class VehicleDetectionRequest(BaseModel):
    junction_id: int = Field(..., description="Junction identifier", ge=1)
    lane_number: int = Field(..., description="Lane number (1-4)", ge=1, le=4)
    fastag_id: str = Field(..., description="FASTag identifier", min_length=1)
    vehicle_type: str = Field("car", description="Type of vehicle")

class JunctionStatusResponse(BaseModel):
    junction_id: int
    junction_name: str
    current_lane_counts: List[Dict[str, Any]]
    latest_cycle: Optional[Dict[str, Any]]
    total_vehicles_today: int

class HealthResponse(BaseModel):
    status: str
    database_connected: bool
    algorithm_version: str
    uptime: str
    error: Optional[str] = None

# API Endpoints

@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint with API information"""
    return {
        "service": "FlexTraff ATCS API",
        "version": "1.0.0",
        "description": "Adaptive Traffic Control System",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health", response_model=HealthResponse)
async def health_check(db: DatabaseService = Depends(get_db_service)):
    """Health check endpoint"""
    try:
        health_data = await db.health_check()
        return HealthResponse(
            status="healthy" if health_data["database_connected"] else "unhealthy",
            database_connected=health_data["database_connected"],
            algorithm_version="ATCS v1.0",
            uptime="Active",
            error=health_data.get("error")
        )
    except Exception as e:
        return HealthResponse(
            status="error",
            database_connected=False,
            algorithm_version="ATCS v1.0",
            uptime="Active",
            error=str(e)
        )

@app.post("/calculate-timing", response_model=TrafficCalculationResponse)
async def calculate_traffic_timing(
    request: LaneCountsRequest,
    calculator: TrafficCalculator = Depends(get_traffic_calculator)
):
    """Calculate optimal traffic light timing based on lane counts"""
    try:
        logger.info(f"📊 Calculating timing for lane counts: {request.lane_counts}")
        
        green_times, cycle_time = await calculator.calculate_green_times(
            request.lane_counts,
            junction_id=request.junction_id
        )
        
        algorithm_info = calculator.get_algorithm_info()
        
        return TrafficCalculationResponse(
            green_times=green_times,
            cycle_time=cycle_time,
            algorithm_info=algorithm_info,
            junction_id=request.junction_id
        )
        
    except Exception as e:
        logger.error(f"❌ Traffic calculation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Traffic calculation failed: {str(e)}")

@app.post("/vehicle-detection")
async def log_vehicle_detection(
    request: VehicleDetectionRequest,
    background_tasks: BackgroundTasks,
    db: DatabaseService = Depends(get_db_service)
):
    """Log vehicle detection event"""
    try:
        # Log vehicle detection in background
        background_tasks.add_task(
            db.log_vehicle_detection,
            request.junction_id,
            request.lane_number,
            request.fastag_id,
            request.vehicle_type
        )
        
        return {
            "status": "success",
            "message": "Vehicle detection logged",
            "junction_id": request.junction_id,
            "lane": request.lane_number,
            "fastag_id": request.fastag_id
        }
        
    except Exception as e:
        logger.error(f"❌ Vehicle detection logging failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to log vehicle detection: {str(e)}")

@app.get("/junctions")
async def get_junctions(db: DatabaseService = Depends(get_db_service)):
    """Get all active junctions"""
    try:
        junctions = await db.get_all_junctions()
        return {"junctions": junctions}
        
    except Exception as e:
        logger.error(f"❌ Failed to get junctions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get junctions: {str(e)}")

@app.get("/junction/{junction_id}/status", response_model=JunctionStatusResponse)
async def get_junction_status(
    junction_id: int,
    db: DatabaseService = Depends(get_db_service)
):
    """Get current status of a specific junction"""
    try:
        # Get current lane counts
        lane_counts = await db.get_current_lane_counts(junction_id, time_window_minutes=5)
        
        # Get latest traffic cycle
        latest_cycle = await db.get_current_traffic_cycle(junction_id)
        
        # Get today's vehicle count
        today_count = await db.get_vehicles_count_by_date(junction_id, date.today())
        
        # Get junction info
        junctions = await db.get_all_junctions()
        junction = next((j for j in junctions if j['id'] == junction_id), None)
        
        if not junction:
            raise HTTPException(status_code=404, detail="Junction not found")
        
        return JunctionStatusResponse(
            junction_id=junction_id,
            junction_name=junction['junction_name'],
            current_lane_counts=lane_counts,
            latest_cycle=latest_cycle,
            total_vehicles_today=today_count
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get junction status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get junction status: {str(e)}")

@app.get("/junction/{junction_id}/live-timing")
async def get_live_timing(
    junction_id: int,
    time_window: int = 5,
    calculator: TrafficCalculator = Depends(get_traffic_calculator),
    db: DatabaseService = Depends(get_db_service)
):
    """Get live traffic timing calculation based on current vehicle counts"""
    try:
        # Get current lane counts from recent detections
        lane_data = await db.get_current_lane_counts(junction_id, time_window_minutes=time_window)
        
        # Extract counts for each lane
        lane_counts = [0, 0, 0, 0]  # Initialize for 4 lanes
        for data in lane_data:
            lane_idx = data['lane_number'] - 1  # Convert to 0-based index
            if 0 <= lane_idx < 4:
                lane_counts[lane_idx] = data['count']
        
        # Calculate optimal timing
        green_times, cycle_time = await calculator.calculate_green_times(
            lane_counts,
            junction_id=junction_id
        )
        
        return {
            "junction_id": junction_id,
            "current_lane_counts": lane_counts,
            "recommended_green_times": green_times,
            "total_cycle_time": cycle_time,
            "time_window_minutes": time_window,
            "algorithm_info": calculator.get_algorithm_info()
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to get live timing: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get live timing: {str(e)}")

@app.get("/junction/{junction_id}/history")
async def get_junction_history(
    junction_id: int,
    limit: int = 10,
    db: DatabaseService = Depends(get_db_service)
):
    """Get recent traffic cycles and detections for a junction"""
    try:
        # Get recent detections
        recent_detections = await db.get_recent_detections_with_signals(junction_id, limit=limit*2)
        
        # Get recent cycles (if available through a method)
        # For now, we'll use get_current_traffic_cycle which gets the latest
        latest_cycle = await db.get_current_traffic_cycle(junction_id)
        
        return {
            "junction_id": junction_id,
            "recent_detections": recent_detections,
            "latest_cycle": latest_cycle,
            "total_records": len(recent_detections)
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to get junction history: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get junction history: {str(e)}")

@app.get("/analytics/daily-summary")
async def get_daily_summary(
    target_date: Optional[date] = None,
    db: DatabaseService = Depends(get_db_service)
):
    """Get daily traffic summary across all junctions"""
    try:
        if target_date is None:
            target_date = date.today()
        
        # Get all junctions
        junctions = await db.get_all_junctions()
        
        summary = []
        for junction in junctions:
            vehicle_count = await db.get_vehicles_count_by_date(junction['id'], target_date)
            summary.append({
                "junction_id": junction['id'],
                "junction_name": junction['junction_name'],
                "total_vehicles": vehicle_count,
                "date": target_date.isoformat()
            })
        
        return {
            "date": target_date.isoformat(),
            "junction_summaries": summary,
            "total_vehicles": sum(s["total_vehicles"] for s in summary)
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to get daily summary: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get daily summary: {str(e)}")

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    from fastapi.responses import JSONResponse
    logger.error(f"HTTP error {exc.status_code}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "status_code": exc.status_code}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    from fastapi.responses import JSONResponse
    logger.error(f"Unexpected error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "status_code": 500}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)