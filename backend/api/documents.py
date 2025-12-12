# backend/api/documents.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.db.database import get_db
from backend.models.document import Document
from backend.api.utils import get_current_user

router = APIRouter(prefix="/api", tags=["documents"])

@router.get("/documents")
def list_documents(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user_email = current_user["email"]
    docs = db.query(Document).join(User).filter(User.email == user_email).order_by(Document.upload_date.desc()).all()
    return [doc.to_dict() for doc in docs]

@router.delete("/documents/{document_id}")
def delete_document(
    doc_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Find document and ownership check
    doc = ( db.query)