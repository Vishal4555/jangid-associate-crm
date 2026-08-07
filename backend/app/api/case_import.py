from io import BytesIO
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.core.security import require_permission
from app.db.database import get_db
from app.models.user import User
from app.schemas.case_import import CaseImportResponse
from app.services.case_import_service import import_cases, template_bytes

router=APIRouter(prefix="/cases/import",tags=["case import"])
MAX_IMPORT_SIZE=2*1024*1024

@router.get("/template")
def download_template(db:Session=Depends(get_db),user:User=Depends(require_permission("cases.create"))):
    return StreamingResponse(BytesIO(template_bytes(db,user)),media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",headers={"Content-Disposition":'attachment; filename="case_import_template.xlsx"'})

@router.post("",response_model=CaseImportResponse)
async def upload_cases(file:UploadFile=File(...),db:Session=Depends(get_db),user:User=Depends(require_permission("cases.create"))):
    if not file.filename or not file.filename.lower().endswith(".xlsx"):raise HTTPException(status_code=415,detail="Only .xlsx files are accepted")
    content=await file.read(MAX_IMPORT_SIZE+1)
    if len(content)>MAX_IMPORT_SIZE:raise HTTPException(status_code=413,detail="Import file exceeds 2 MB")
    return import_cases(db,user,content)
