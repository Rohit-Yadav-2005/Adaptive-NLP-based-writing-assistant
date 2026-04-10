"""
Main FastAPI Application (Enterprise V2)
Supports Auth, Team Workspaces, and Version-Controlled Documentation.
"""

import os
import logging
from datetime import timedelta
from dotenv import load_dotenv

from fastapi import FastAPI, HTTPException, Depends, status, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Dict, Any
from sqlalchemy import func
from sqlalchemy.orm import Session

# Load env and initialize DB
load_dotenv()
from .database import init_enterprise_db, get_db
init_enterprise_db()

from .models import User, Organization, Document, DocumentVersion, ActivityLog, Invitation, Folder, VaultDocument, Comment
from .auth import (
    get_password_hash, 
    verify_password, 
    create_access_token, 
    get_current_user,
    oauth2_scheme,
    SECRET_KEY,
    ALGORITHM
)
from jose import jwt, JWTError # Using jose for decoding in dependency

from .style import extract_features, update_user_profile
from .llm_engine import analyze_and_improve_with_llm

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Adaptive Writing Assistant (Enterprise v2)",
    description="Professional writing platform with team collaboration and versioning.",
    version="2.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------------------------
# Pydantic Schemas
# -------------------------------------------------------------------
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None

class Token(BaseModel):
    access_token: str
    token_type: str

class WorkspaceCreate(BaseModel):
    name: str

class FolderCreate(BaseModel):
    name: str
    org_id: int

class DocumentCreate(BaseModel):
    title: str
    content: str
    org_id: Optional[int] = None
    folder_id: Optional[int] = None
    writing_type: Optional[str] = "general"

class DocumentUpdate(BaseModel):
    content: str
    change_summary: Optional[str] = "Updated content"

class AnalyzeRequest(BaseModel):
    text: str
    target_style: Optional[str] = "general"

class InviteRequest(BaseModel):
    email: str

class ActivityRead(BaseModel):
    id: int
    action: str
    details: Optional[str] = None
    created_at: Any
    user_email: str
    document_title: Optional[str] = None

    class Config:
        from_attributes = True

class CommentCreate(BaseModel):
    content: str
    document_id: int

class CommentRead(BaseModel):
    id: int
    content: str
    created_at: Any
    user_email: str
    
    class Config:
        from_attributes = True

# -------------------------------------------------------------------
# Dependencies
# -------------------------------------------------------------------
def get_authenticated_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    from jose import jwt
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except Exception:
        raise credentials_exception
    
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
    return user

def log_activity(db: Session, user_id: int, org_id: int, action: str, details: str = None, doc_id: int = None):
    new_log = ActivityLog(
        user_id=user_id,
        org_id=org_id,
        action=action,
        details=details,
        document_id=doc_id
    )
    db.add(new_log)
    db.commit()

# -------------------------------------------------------------------
# Auth Endpoints
# -------------------------------------------------------------------
@app.post("/api/v2/auth/register", response_model=Token)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user_in.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    new_user = User(
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Create a default workspace for the user
    default_org = Organization(name=f"{new_user.full_name or 'My'} Workspace", owner_id=new_user.id)
    db.add(default_org)
    new_user.organizations.append(default_org)
    db.commit()
    
    access_token = create_access_token(data={"sub": new_user.email})
    
    # Log activity
    log_activity(db, new_user.id, default_org.id, "User Registered", "Initialized Workspace")
    
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/api/v2/auth/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

# -------------------------------------------------------------------
# Core AI Endpoints
# -------------------------------------------------------------------
@app.post("/api/v2/analyze")
def analyze_text(request: AnalyzeRequest, user: User = Depends(get_authenticated_user), db: Session = Depends(get_db)):
    """Analyze text using the LLM engine with user-specific style profile and Vault context."""
    
    # 1. Extract style profile
    features = extract_features(request.text)
    style_profile = update_user_profile(f"user_{user.id}", features)
    
    # 2. Retrieve relevant context from Research Vault if available
    org_id = user.organizations[0].id if user.organizations else None
    vault_context = []
    if org_id:
        try:
            from .vault import search_vault
            vault_context = search_vault(request.text, org_id)
        except Exception:
            # Vault dependencies (pypdf, chromadb) may not be installed - skip gracefully
            vault_context = []
    
    try:
        # Pass vault research context to LLM
        llm_response = analyze_and_improve_with_llm(
            request.text, 
            style_profile, 
            target_style=request.target_style,
            research_context="\n".join(vault_context) if vault_context else None
        )
        
        # Log activity
        if org_id:
            log_activity(db, user.id, org_id, "AI Analysis", f"Performed {request.target_style} analysis")
        
        return {
            **llm_response,
            "style_profile": style_profile,
            "context_used": len(vault_context) > 0
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -------------------------------------------------------------------
# Document & Workspace Management
# -------------------------------------------------------------------
@app.get("/api/v2/workspaces")
def list_workspaces(user: User = Depends(get_authenticated_user)):
    return [{"id": org.id, "name": org.name, "role": "owner" if org.owner_id == user.id else "member"} for org in user.organizations]

# --- Folder Endpoints ---
@app.get("/api/v2/folders")
def list_folders(org_id: int, user: User = Depends(get_authenticated_user), db: Session = Depends(get_db)):
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org or user not in org.members:
        raise HTTPException(status_code=403, detail="Forbidden")
    return [{"id": f.id, "name": f.name, "org_id": f.org_id, "created_at": str(f.created_at)} for f in org.folders]

@app.get("/api/v2/workspaces/activity", response_model=List[ActivityRead])
def get_activity(org_id: int, user: User = Depends(get_authenticated_user), db: Session = Depends(get_db)):
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org or user not in org.members:
        raise HTTPException(status_code=403, detail="Forbidden")
    
    logs = db.query(ActivityLog).filter(ActivityLog.org_id == org_id).order_by(ActivityLog.created_at.desc()).limit(50).all()
    # Simple transform to schema
    return [
        {
            "id": l.id,
            "action": l.action,
            "details": l.details,
            "created_at": l.created_at,
            "user_email": l.user.email if l.user else "System",
            "document_title": l.document.title if l.document else None
        } for l in logs
    ]

@app.post("/api/v2/folders")
def create_folder(folder_in: FolderCreate, user: User = Depends(get_authenticated_user), db: Session = Depends(get_db)):
    org = db.query(Organization).filter(Organization.id == folder_in.org_id).first()
    if not org or user not in org.members:
        raise HTTPException(status_code=403, detail="Forbidden")
    
    new_folder = Folder(name=folder_in.name, org_id=org.id)
    db.add(new_folder)
    db.commit()
    db.refresh(new_folder)
    
    log_activity(db, user.id, org.id, "Created Folder", f"Folder: {new_folder.name}")
    return {"id": new_folder.id, "name": new_folder.name, "org_id": new_folder.org_id, "created_at": str(new_folder.created_at)}

@app.post("/api/v2/workspaces/{org_id}/invite")
def invite_member(org_id: int, invite_in: InviteRequest, user: User = Depends(get_authenticated_user), db: Session = Depends(get_db)):
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org or user.id != org.owner_id:
        raise HTTPException(status_code=403, detail="Only owner can invite")
    
    import secrets
    token = secrets.token_urlsafe(16)
    new_invite = Invitation(email=invite_in.email, token=token, org_id=org.id)
    db.add(new_invite)
    db.commit()
    
    log_activity(db, user.id, org.id, "Sent Invitation", f"To: {invite_in.email}")
    return {"invite_link": f"/join/{token}"}

@app.post("/api/v2/documents")
def create_document(doc_in: DocumentCreate, user: User = Depends(get_authenticated_user), db: Session = Depends(get_db)):
    # Simple check if user belongs to the org
    org = db.query(Organization).filter(Organization.id == doc_in.org_id).first()
    if not org or user not in org.members:
        # Default to first available org if none provided or unauthorized
        org = user.organizations[0]
        
    new_doc = Document(
        title=doc_in.title,
        content=doc_in.content,
        user_id=user.id,
        org_id=org.id,
        folder_id=doc_in.folder_id,
        writing_type=doc_in.writing_type
    )
    db.add(new_doc)
    db.commit()
    db.refresh(new_doc)
    
    # Save first version
    first_version = DocumentVersion(
        document_id=new_doc.id,
        content_snapshot=doc_in.content,
        change_summary="Initial commit"
    )
    db.add(first_version)
    db.commit()
    
    log_activity(db, user.id, org.id, "Created Document", f"Project: {new_doc.title}", doc_id=new_doc.id)
    return {"id": new_doc.id, "title": new_doc.title, "content": new_doc.content, 
            "writing_type": new_doc.writing_type, "folder_id": new_doc.folder_id, 
            "org_id": new_doc.org_id, "created_at": str(new_doc.created_at), "updated_at": str(new_doc.updated_at)}

@app.get("/api/v2/documents")
def list_documents(org_id: int, user: User = Depends(get_authenticated_user), db: Session = Depends(get_db)):
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org or user not in org.members:
        raise HTTPException(status_code=403, detail="Forbidden")
    return [
        {"id": d.id, "title": d.title, "content": d.content, "writing_type": d.writing_type, 
         "folder_id": d.folder_id, "org_id": d.org_id, "user_id": d.user_id,
         "created_at": str(d.created_at), "updated_at": str(d.updated_at)}
        for d in db.query(Document).filter(Document.org_id == org_id).all()
    ]

@app.put("/api/v2/documents/{doc_id}")
def update_document(doc_id: int, update: DocumentUpdate, user: User = Depends(get_authenticated_user), db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Not found")
    
    # Check permission
    org = db.query(Organization).filter(Organization.id == doc.org_id).first()
    if user not in org.members:
        raise HTTPException(status_code=403, detail="Forbidden")
    
    # Update current content
    doc.content = update.content
    
    # Create version history
    new_version = DocumentVersion(
        document_id=doc.id,
        content_snapshot=update.content,
        change_summary=update.change_summary
    )
    db.add(new_version)
    db.commit()
    
    log_activity(db, user.id, org.id, "Pushed Commit", f"Summary: {update.change_summary}", doc_id=doc.id)
    return {"status": "success", "version_id": new_version.id}

@app.get("/api/v2/documents/{doc_id}/history")
def get_document_history(doc_id: int, user: User = Depends(get_authenticated_user), db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Not found")
    
    org = db.query(Organization).filter(Organization.id == doc.org_id).first()
    if user not in org.members:
        raise HTTPException(status_code=403, detail="Forbidden")
        
    return [{"id": v.id, "document_id": v.document_id, "content_snapshot": v.content_snapshot, 
              "change_summary": v.change_summary, "created_at": str(v.created_at)} 
             for v in doc.versions]

# --- Research Vault Endpoints ---
@app.post("/api/v2/vault/upload")
async def upload_to_vault(org_id: int, file: UploadFile = File(...), user: User = Depends(get_authenticated_user), db: Session = Depends(get_db)):
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org or user not in org.members:
        raise HTTPException(status_code=403, detail="Forbidden")
    
    os.makedirs("data/vault", exist_ok=True)
    file_path = f"data/vault/{file.filename}"
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())
    
    from backend.vault import add_document_to_vault
    metadata = {"org_id": org.id, "filename": file.filename}
    success = add_document_to_vault(file_path, f"org_{org.id}_{file.filename}", metadata)
    
    if success:
        new_vdoc = VaultDocument(filename=file.filename, file_path=file_path, org_id=org.id)
        db.add(new_vdoc)
        db.commit()
        log_activity(db, user.id, org.id, "Vault Upload", f"File: {file.filename}")
        return {"status": "success"}
    else:
        raise HTTPException(status_code=500, detail="Failed to index document")

@app.get("/api/v2/vault")
def list_vault(org_id: int, user: User = Depends(get_authenticated_user), db: Session = Depends(get_db)):
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org or user not in org.members:
        raise HTTPException(status_code=403, detail="Forbidden")
    return org.vault_documents

# --- Analytics Endpoint ---
@app.get("/api/v2/analytics")
def get_analytics(org_id: int, user: User = Depends(get_authenticated_user), db: Session = Depends(get_db)):
    # Returns word count trends over last 7 days from activity logs
    from datetime import datetime, timedelta
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    
    # This is a mockup; in a real app we'd parse "details" for actual word counts
    # For now, let's return count of commits per day
    stats = db.query(
        func.date(ActivityLog.created_at).label("day"),
        func.count(ActivityLog.id).label("commits")
    ).filter(
        ActivityLog.org_id == org_id,
        ActivityLog.created_at >= seven_days_ago
    ).group_by("day").all()
    
    return [{"day": s.day, "value": s.commits} for s in stats]

# --- Comment Endpoints ---
@app.post("/api/v2/comments")
def add_comment(comment_in: CommentCreate, user: User = Depends(get_authenticated_user), db: Session = Depends(get_db)):
    new_comment = Comment(
        content=comment_in.content,
        user_id=user.id,
        document_id=comment_in.document_id
    )
    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)
    return new_comment

@app.get("/api/v2/documents/{doc_id}/comments")
def list_comments(doc_id: int, user: User = Depends(get_authenticated_user), db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Not found")
    return [{
        "id": c.id, 
        "content": c.content, 
        "created_at": c.created_at, 
        "user_email": c.user.email
    } for c in doc.comments]

# -------------------------------------------------------------------
# Legacy Health Check
# -------------------------------------------------------------------
@app.get("/")
def health_check():
    return {"status": "enterprise-ready", "version": "2.1.0"}