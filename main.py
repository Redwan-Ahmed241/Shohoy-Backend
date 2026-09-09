from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import time

import config
from routers import (
    alerts_router,
    shelters_router,
    requests_router,
    campaigns_router,
    contacts_router,
    volunteers_router,
    warehouse_router,
    auth_router,
)

# 1. Create FastAPI Application Instance
app = FastAPI(
    title=config.PROJECT_NAME,
    version=config.VERSION,
    description=config.DESCRIPTION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{config.API_V1_PREFIX}/openapi.json"
)

# 2. CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_origin_regex=config.CORS_ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. Performance / Latency Header Middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    response.headers["X-Process-Time"] = f"{time.time() - start_time:.4f}s"
    return response

# 4. Register Domain Routers
app.include_router(alerts_router, prefix=config.API_V1_PREFIX)
app.include_router(shelters_router, prefix=config.API_V1_PREFIX)
app.include_router(requests_router, prefix=config.API_V1_PREFIX)
app.include_router(campaigns_router, prefix=config.API_V1_PREFIX)
app.include_router(contacts_router, prefix=config.API_V1_PREFIX)
app.include_router(volunteers_router, prefix=config.API_V1_PREFIX)
app.include_router(warehouse_router, prefix=config.API_V1_PREFIX)
app.include_router(auth_router, prefix=config.API_V1_PREFIX)

# 5. Root & Health Check Endpoints
@app.get("/", tags=["Root"])
def root():
    return {
        "service": config.PROJECT_NAME,
        "status": "online",
        "version": config.VERSION,
        "database": "supabase_postgresql" if config.USE_SUPABASE else "in_memory_mock",
        "docs": "/docs",
        "endpoints": {
            "alerts": f"{config.API_V1_PREFIX}/alerts",
            "shelters": f"{config.API_V1_PREFIX}/shelters",
            "requests": f"{config.API_V1_PREFIX}/requests",
            "campaigns": f"{config.API_V1_PREFIX}/campaigns",
            "contacts": f"{config.API_V1_PREFIX}/contacts",
            "volunteers": f"{config.API_V1_PREFIX}/volunteers/profile",
            "warehouse": f"{config.API_V1_PREFIX}/warehouse/inventory"
        }
    }

@app.get("/health", tags=["Health"])
def health_check():
    db_status = "supabase_connected" if config.USE_SUPABASE else "in_memory_ready"
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "database": db_status
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
