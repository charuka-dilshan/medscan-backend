from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from groq_service import parse_prescription_text
from pydantic import BaseModel
import uvicorn

app = FastAPI(title="MedScan AI Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "MedScan AI Backend is operational."}

if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)

class OCRRequest(BaseModel):
    raw_text: str

@app.post("/parse-prescription")
def parse_prescription(request: OCRRequest):
    try:
        result = parse_prescription_text(request.raw_text)
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))