from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from scans.routes import router as scan_router


app = FastAPI(
    title="MedScan AI Backend",
    version="1.0.0"
)


# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Register Routes

app.include_router(
    scan_router,
    prefix="/scan",
    tags=["Scan"]
)


@app.get("/")
async def root():
    return {
        "message": "MedScan AI Backend Running"
    }