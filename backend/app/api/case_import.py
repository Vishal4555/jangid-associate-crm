from io import BytesIO
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.core.security import require_permission
from app.db.database import get_db
from app.models.user import User
from app.schemas.case_import import CaseImportResponse, ImportCommitRequest, ImportCommitResponse, ImportPreviewResponse
from app.services.case_import_service import import_cases, template_bytes
from app.services.smart_case_import_service import commit_import, preview_import, resume_import

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

@router.post("/preview",response_model=ImportPreviewResponse)
async def preview_cases(file:UploadFile=File(...),db:Session=Depends(get_db),user:User=Depends(require_permission("cases.create"))):
    if not file.filename or not file.filename.lower().endswith(".xlsx"):raise HTTPException(status_code=415,detail="Only .xlsx files are accepted")
    content=await file.read(MAX_IMPORT_SIZE+1)
    if len(content)>MAX_IMPORT_SIZE:raise HTTPException(status_code=413,detail="Import file exceeds 2 MB")
    try:return preview_import(db,user,content,file.filename)
    except ValueError as exc:raise HTTPException(status_code=422,detail=str(exc)) from exc
    except Exception as exc:raise HTTPException(status_code=422,detail="Invalid XLSX file") from exc

@router.post("/commit",response_model=ImportCommitResponse)
def commit_cases(payload:ImportCommitRequest,db:Session=Depends(get_db),user:User=Depends(require_permission("cases.create"))):
    try:return commit_import(db,user,payload.import_token,payload.rows)
    except PermissionError as exc:raise HTTPException(status_code=404,detail=str(exc)) from exc

@router.get("/resume",response_model=ImportPreviewResponse)
def resume_cases(db:Session=Depends(get_db),user:User=Depends(require_permission("cases.create"))):
    try:return resume_import(db,user)
    except PermissionError as exc:raise HTTPException(status_code=404,detail=str(exc)) from exc
