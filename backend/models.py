from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Boolean, Table
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime

Base = declarative_base()

# Many-to-Many relationship between Users and Organizations
org_members = Table(
    'org_members',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('org_id', Integer, ForeignKey('organizations.id'), primary_key=True),
    Column('role', String, default='member') # 'admin' or 'member'
)

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    organizations = relationship("Organization", secondary=org_members, back_populates="members")
    authored_documents = relationship("Document", back_populates="author")
    activities = relationship("ActivityLog", back_populates="user")

class Organization(Base):
    __tablename__ = 'organizations'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    owner_id = Column(Integer, ForeignKey('users.id'))
    
    # Relationships
    members = relationship("User", secondary=org_members, back_populates="organizations")
    documents = relationship("Document", back_populates="organization")
    folders = relationship("Folder", back_populates="organization", cascade="all, delete-orphan")
    activities = relationship("ActivityLog", back_populates="organization", cascade="all, delete-orphan")
    invitations = relationship("Invitation", back_populates="organization", cascade="all, delete-orphan")
    vault_documents = relationship("VaultDocument", back_populates="organization", cascade="all, delete-orphan")

class Folder(Base):
    __tablename__ = 'folders'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    org_id = Column(Integer, ForeignKey('organizations.id'))
    organization = relationship("Organization", back_populates="folders")
    documents = relationship("Document", back_populates="folder")

class Document(Base):
    __tablename__ = 'documents'
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True, nullable=False)
    content = Column(Text)
    writing_type = Column(String, default="general") # academic, technical, email, etc.
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user_id = Column(Integer, ForeignKey('users.id'))
    org_id = Column(Integer, ForeignKey('organizations.id'))
    folder_id = Column(Integer, ForeignKey('folders.id'), nullable=True)
    
    # Relationships
    author = relationship("User", back_populates="authored_documents")
    organization = relationship("Organization", back_populates="documents")
    folder = relationship("Folder", back_populates="documents")
    versions = relationship("DocumentVersion", back_populates="document", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="document", cascade="all, delete-orphan")

class DocumentVersion(Base):
    __tablename__ = 'document_versions'
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey('documents.id'))
    content_snapshot = Column(Text, nullable=False)
    change_summary = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    document = relationship("Document", back_populates="versions")

class ActivityLog(Base):
    __tablename__ = 'activity_logs'
    id = Column(Integer, primary_key=True, index=True)
    action = Column(String, nullable=False) # e.g. "Created Document", "Applied AI Suggestions"
    details = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user_id = Column(Integer, ForeignKey('users.id'))
    org_id = Column(Integer, ForeignKey('organizations.id'))
    document_id = Column(Integer, ForeignKey('documents.id'), nullable=True)
    
    user = relationship("User", back_populates="activities")
    organization = relationship("Organization", back_populates="activities")
    document = relationship("Document")

class Invitation(Base):
    __tablename__ = 'invitations'
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, index=True, nullable=False)
    token = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    accepted = Column(Boolean, default=False)
    
    org_id = Column(Integer, ForeignKey('organizations.id'))
    organization = relationship("Organization", back_populates="invitations")

class VaultDocument(Base):
    __tablename__ = 'vault_documents'
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    file_path = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    org_id = Column(Integer, ForeignKey('organizations.id'))
    organization = relationship("Organization", back_populates="vault_documents")

class Comment(Base):
    __tablename__ = 'comments'
    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user_id = Column(Integer, ForeignKey('users.id'))
    document_id = Column(Integer, ForeignKey('documents.id'))
    
    user = relationship("User")
    document = relationship("Document", back_populates="comments")
