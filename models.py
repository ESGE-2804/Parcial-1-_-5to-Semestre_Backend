from datetime import datetime
from typing import List, Optional
from sqlmodel import Field, SQLModel, Relationship

class Usuario(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    email: str = Field(unique=True, index=True)
    password_hash: str
    
    videos: List["Video"] = Relationship(back_populates="autor", sa_relationship_kwargs={"cascade": "all, delete-orphan"})
    comentarios: List["Comentario"] = Relationship(back_populates="autor", sa_relationship_kwargs={"cascade": "all, delete-orphan"})

class Video(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    description: Optional[str] = None
    video_url: str
    thumbnail_url: str
    views: int = Field(default=0)
    user_id: int = Field(foreign_key="usuario.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    autor: Optional[Usuario] = Relationship(back_populates="videos")
    comentarios: List["Comentario"] = Relationship(back_populates="video", sa_relationship_kwargs={"cascade": "all, delete-orphan"})

class Comentario(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    content: str
    user_id: int = Field(foreign_key="usuario.id")
    video_id: int = Field(foreign_key="video.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    autor: Optional[Usuario] = Relationship(back_populates="comentarios")
    video: Optional[Video] = Relationship(back_populates="comentarios")