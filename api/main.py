from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import shutil
from architect import ArchitectOrchestrator
from pydantic import BaseModel

app = FastAPI()
orchestrator = ArchitectOrchestrator()

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class DeploymentRequest(BaseModel):
    resource_group: str
    parameters: dict = None

@app.post("/process-architecture")
async def process_architecture(file: UploadFile = File(...)):
    try:
        # Save uploaded file
        image_path = f"uploads/{file.filename}"
        Path("uploads").mkdir(exist_ok=True)
        
        with open(image_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Run pipeline
        result = orchestrator.run_pipeline(image_path)
        
        if result["status"] == "error":
            raise HTTPException(status_code=400, detail=result["message"])
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/deploy-template")
async def deploy_template(template_path: str, request: DeploymentRequest):
    """Deploy ARM template to Azure"""
    try:
        result = orchestrator.deploy_resources(
            template_path=template_path,
            resource_group=request.resource_group,
            parameters=request.parameters
        )
        
        if result["status"] == "error":
            raise HTTPException(status_code=400, detail=result["message"])
            
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status")
async def status_check():
    return {"status": "ready"}