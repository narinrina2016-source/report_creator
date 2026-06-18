from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from app.api import deps
from app.models.report import Report, Approval, ExternalDispatch
from app.models.template import Template
from app.schemas.report import Report as ReportSchema, ReportCreate, ApprovalCreate

router = APIRouter()

@router.post("/", response_model=ReportSchema)
def create_report(
    *,
    db: Session = Depends(deps.get_db),
    report_in: ReportCreate
) -> Any:
    """
    Create a new report from an uploaded PDF.
    """
    report = Report(
        title=report_in.title,
        template_id=report_in.template_id,
        created_by=1, # Mock user ID
        data=report_in.data or {},
        status="Draft",
        pdf_url=report_in.pdf_url,
        generated_file_path=report_in.pdf_url # Using the same field for compatibility with frontend
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    
    # Auto Reference Numbering logic
    year = datetime.now().strftime("%y")
    ref_number = f"{report.id:03d}/{year} របក"
    
    report_data = dict(report.data) if report.data else {}
    report_data["ReferenceNumber"] = ref_number
    report.data = report_data
    
    db.commit()
    db.refresh(report)
        
    return report

@router.put("/{report_id}", response_model=ReportSchema)
def update_report(
    *,
    report_id: int,
    db: Session = Depends(deps.get_db),
    report_in: ReportCreate
) -> Any:
    """
    Update an existing report (no document generation).
    """
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
        
    report.title = report_in.title
    report.template_id = report_in.template_id
    
    # Maintain or generate Reference Number
    report_data = dict(report_in.data) if report_in.data else {}
    if "ReferenceNumber" not in report_data:
        year = datetime.now().strftime("%y")
        report_data["ReferenceNumber"] = f"{report.id:03d}/{year} របក"
        
    report.data = report_data
    report.annotations = [] # Clear annotations since the document might be changing
    
    if report_in.pdf_url:
        report.pdf_url = report_in.pdf_url
        report.generated_file_path = report_in.pdf_url
        
    db.commit()
    db.refresh(report)
    return report


@router.post("/{report_id}/approve", response_model=ReportSchema)
def approve_report(
    *,
    report_id: int,
    db: Session = Depends(deps.get_db),
    approval_in: ApprovalCreate
) -> Any:
    """
    Approve or reject a report (Workflow).
    """
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
        
    approval = Approval(
        report_id=report.id,
        approver_id=1, # Mock user ID
        status=approval_in.status,
        comments=approval_in.comments
    )
    db.add(approval)
    
    # Update report status based on workflow rules
    report.status = approval_in.status
            
    db.commit()
    db.refresh(report)
    
    return report

@router.get("/", response_model=List[ReportSchema])
def get_reports(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100
) -> Any:
    """
    List all reports.
    """
    reports = db.query(Report).offset(skip).limit(limit).all()
    return reports

import mammoth
from pydantic import BaseModel

class HTMLUpdate(BaseModel):
    html_content: str

class AnnotationsUpdate(BaseModel):
    annotations: list

@router.get("/{report_id}/annotations")
def get_report_annotations(
    report_id: int,
    db: Session = Depends(deps.get_db)
):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return {"annotations": report.annotations or []}

@router.put("/{report_id}/annotations")
def update_report_annotations(
    report_id: int,
    data: AnnotationsUpdate,
    db: Session = Depends(deps.get_db)
):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
        
    report.annotations = data.annotations
    db.commit()
    return {"message": "Annotations updated", "annotations": report.annotations}

@router.get("/{report_id}/html")
def get_report_html(
    report_id: int,
    db: Session = Depends(deps.get_db)
):
    """
    Get the HTML version of the report for the In-App Editor.
    """
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
        
    if report.html_content:
        return {
            "html_content": report.html_content,
            "original_html_content": report.original_html_content
        }
            
    return {"html_content": "<p>ទិន្នន័យឯកសារមិនអាចទាញយកបានទេ។</p>"}

@router.put("/{report_id}/html")
def update_report_html(
    report_id: int,
    data: HTMLUpdate,
    db: Session = Depends(deps.get_db)
):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
        
    report.html_content = data.html_content
    db.commit()
        
    return {"message": "Saved successfully"}


class AssignUser(BaseModel):
    user_id: int

@router.post("/{report_id}/assign_editor")
def assign_editor(
    report_id: int,
    data: AssignUser,
    db: Session = Depends(deps.get_db)
):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
        
    report.editor_id = data.user_id
    report.status = "Sent to Editor"
    
    db.add(Approval(report_id=report.id, approver_id=data.user_id, status="Sent to Editor", comments="Assigned to Editor"))
    
    db.commit()
    return {"message": "Assigned editor successfully"}

@router.post("/{report_id}/assign_president")
def assign_president(
    report_id: int,
    data: AssignUser,
    db: Session = Depends(deps.get_db)
):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
        
    report.president_id = data.user_id
    report.status = "Sent to President"
    
    db.add(Approval(report_id=report.id, approver_id=data.user_id, status="Sent to President", comments="Assigned to President"))
    
    db.commit()
    return {"message": "Assigned president successfully"}

@router.post("/{report_id}/assign_department_head")
def assign_department_head(
    report_id: int,
    data: AssignUser,
    db: Session = Depends(deps.get_db)
):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
        
    report.department_head_id = data.user_id
    report.status = "Sent to Department Head"
    
    db.add(Approval(report_id=report.id, approver_id=data.user_id, status="Sent to Department Head", comments="Assigned to Department Head"))
    
    db.commit()
    return {"message": "Assigned department head successfully"}

@router.post("/{report_id}/assign_admin")
def assign_admin(
    report_id: int,
    data: AssignUser,
    db: Session = Depends(deps.get_db)
):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
        
    report.admin_id = data.user_id
    report.status = "Sent to Admin"
    
    db.add(Approval(report_id=report.id, approver_id=data.user_id, status="Sent to Admin", comments="Assigned to Admin"))
    
    db.commit()
    return {"message": "Assigned admin successfully"}

class FinalizeData(BaseModel):
    reference_number: str
    include_qr: bool

import qrcode
from xhtml2pdf import pisa
import uuid

@router.post("/{report_id}/finalize")
def finalize_report(
    report_id: int,
    data: FinalizeData,
    db: Session = Depends(deps.get_db)
):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
        
    report.reference_number = data.reference_number
    report.status = "Finalized"
    
    db.add(Approval(report_id=report.id, approver_id=1, status="Finalized", comments=f"Issued Reference Number: {data.reference_number}"))
    db.commit()
    return {"message": "Report finalized successfully", "pdf_path": report.generated_file_path}

from fastapi.responses import FileResponse
from fastapi.responses import RedirectResponse
import os

@router.get("/{report_id}/download")
def download_report(
    report_id: int,
    db: Session = Depends(deps.get_db)
):
    """
    Download or redirect to the uploaded PDF report.
    """
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report or not report.pdf_url:
        raise HTTPException(status_code=404, detail="Report file not found")
        
    # If it's a Supabase storage URL, redirect to it
    if report.pdf_url.startswith("http"):
        return RedirectResponse(url=report.pdf_url)
        
    # Legacy local files (if any remain)
    serve_path = report.generated_file_path
    if not serve_path or not os.path.exists(serve_path):
        raise HTTPException(status_code=404, detail="Physical file missing on server")

    return FileResponse(
        path=serve_path,
        filename=os.path.basename(serve_path),
        media_type="application/pdf",
        content_disposition_type="inline"
    )

@router.get("/{report_id}/verify")
def verify_report(
    report_id: int,
    db: Session = Depends(deps.get_db)
):
    """
    Public endpoint for verifying a report via QR Code.
    """
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report or report.status != "Finalized":
        raise HTTPException(status_code=404, detail="Invalid or Unverified Document")
        
    return {
        "id": report.id,
        "title": report.template.name if report.template else "ឯកសាររដ្ឋបាល",
        "reference_number": report.reference_number,
        "finalized_date": report.created_at, # Or finalized date if you add it
        "creator": report.creator.full_name if report.creator else None,
        "editor": report.editor.full_name if report.editor else None,
        "department_head": report.department_head.full_name if report.department_head else None,
        "admin": report.admin.full_name if report.admin else None,
        "president": report.president.full_name if report.president else None,
    }

@router.get("/{report_id}/tracking")
def get_report_tracking(
    report_id: int,
    db: Session = Depends(deps.get_db)
):
    """
    Get the chronological tracking history of a report.
    """
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
        
    approvals = db.query(Approval).filter(Approval.report_id == report_id).order_by(Approval.created_at.asc()).all()
    
    tracking = []
    # Add initial creation
    tracking.append({
        "status": "Created",
        "action": "របាយការណ៍ត្រូវបានបង្កើត (Draft)",
        "timestamp": report.created_at,
        "user": report.creator.full_name if report.creator else "អ្នកប្រើប្រាស់",
        "comments": None
    })
    
    for app in approvals:
        tracking.append({
            "status": app.status,
            "action": app.status,
            "timestamp": app.created_at,
            "user": app.approver.full_name if app.approver else "អ្នកប្រើប្រាស់",
            "comments": app.comments
        })
        
    # Also add dispatch info if any
    dispatches = db.query(ExternalDispatch).filter(ExternalDispatch.report_id == report_id).order_by(ExternalDispatch.sent_at.asc()).all()
    for disp in dispatches:
        tracking.append({
            "status": "Dispatched",
            "action": f"បញ្ជូនទៅ {disp.institution_name}",
            "timestamp": disp.sent_at,
            "user": "រដ្ឋបាល/អ្នករត់សំបុត្រ",
            "comments": f"តាម: {disp.dispatch_method}"
        })
        if disp.status == "Received" and disp.received_at:
            tracking.append({
                "status": "Received External",
                "action": f"ស្ថាប័ន {disp.institution_name} បានទទួល",
                "timestamp": disp.received_at,
                "user": "ស្ថាប័នខាងក្រៅ",
                "comments": "បានទទួលឯកសាររួចរាល់"
            })
            
    # Sort again by timestamp just in case
    tracking.sort(key=lambda x: x["timestamp"])
        
    return tracking

from pydantic import BaseModel
from typing import Optional

class DispatchCreate(BaseModel):
    institution_name: str
    dispatch_method: str
    dispatch_photo: Optional[str] = None

@router.post("/{report_id}/dispatch")
def create_dispatch(
    report_id: int,
    data: DispatchCreate,
    db: Session = Depends(deps.get_db)
):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report or report.status != "Finalized":
        raise HTTPException(status_code=400, detail="Report must be finalized to dispatch")
        
    dispatch = ExternalDispatch(
        report_id=report_id,
        institution_name=data.institution_name,
        dispatch_method=data.dispatch_method,
        status="Sent",
        dispatch_photo=data.dispatch_photo
    )
    db.add(dispatch)
    db.commit()
    db.refresh(dispatch)
    return dispatch

@router.get("/{report_id}/dispatches")
def get_dispatches(
    report_id: int,
    db: Session = Depends(deps.get_db)
):
    dispatches = db.query(ExternalDispatch).filter(ExternalDispatch.report_id == report_id).all()
    return dispatches

class ReceiveDispatch(BaseModel):
    receive_photo: Optional[str] = None

@router.put("/dispatches/{dispatch_id}/receive")
def receive_dispatch(
    dispatch_id: int,
    data: ReceiveDispatch,
    db: Session = Depends(deps.get_db)
):
    dispatch = db.query(ExternalDispatch).filter(ExternalDispatch.id == dispatch_id).first()
    if not dispatch:
        raise HTTPException(status_code=404, detail="Dispatch not found")
        
    dispatch.status = "Received"
    dispatch.received_at = datetime.utcnow()
    if data.receive_photo:
        dispatch.receive_photo = data.receive_photo
        
    db.commit()
    return {"message": "Marked as received successfully"}
