from typing import Optional
from fastapi import APIRouter, HTTPException, status, Form, File, UploadFile, Depends
from pydantic import BaseModel
from sqlmodel import select
from db import SessionDep
from models import Video, Comentario, Usuario
from app.s3_helper import upload_media_to_s3
from app.routers.users import get_current_user

router = APIRouter(prefix="/videos", tags=["Videos y Comentarios"])

class VideoUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None

class ComentarioCreate(BaseModel):
    content: str

@router.post("", status_code=status.HTTP_201_CREATED)
async def create_video(
    session: SessionDep,
    title: str = Form(...),
    description: Optional[str] = Form(None),
    video_file: UploadFile = File(...),
    thumbnail_file: UploadFile = File(...),
    current_user: Usuario = Depends(get_current_user)
):
    if not video_file.filename.lower().endswith(".mp4"):
        raise HTTPException(status_code=400, detail="El video debe ser en formato MP4")

    video_bytes = await video_file.read()
    thumb_bytes = await thumbnail_file.read()

    video_url = upload_media_to_s3(video_bytes, video_file.filename, video_file.content_type, is_video=True)
    thumb_url = upload_media_to_s3(thumb_bytes, thumbnail_file.filename, thumbnail_file.content_type, is_video=False)

    nuevo_video = Video(
        title=title,
        description=description,
        video_url=video_url,
        thumbnail_url=thumb_url,
        user_id=current_user.id
    )
    session.add(nuevo_video)
    session.commit()
    session.refresh(nuevo_video)
    return nuevo_video

@router.get("")
def list_videos(session: SessionDep):
    return session.exec(select(Video).order_by(Video.id.desc())).all()

@router.get("/{id}")
def get_video_detail(id: int, session: SessionDep):
    video = session.get(Video, id)
    if not video:
        raise HTTPException(status_code=404, detail="Video no encontrado")
    video.views += 1
    session.add(video)
    session.commit()
    session.refresh(video)
    return video

@router.put("/{id}")
def update_video(id: int, data: VideoUpdate, session: SessionDep, current_user: Usuario = Depends(get_current_user)):
    video = session.get(Video, id)
    if not video:
        raise HTTPException(status_code=404, detail="Video no encontrado")
    if video.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="No autorizado para editar este video")
    
    if data.title is not None:
        video.title = data.title
    if data.description is not None:
        video.description = data.description
        
    session.add(video)
    session.commit()
    session.refresh(video)
    return video

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_video(id: int, session: SessionDep, current_user: Usuario = Depends(get_current_user)):
    video = session.get(Video, id)
    if not video:
        raise HTTPException(status_code=404, detail="Video no encontrado")
    if video.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="No autorizado para eliminar este video")
    
    session.delete(video)
    session.commit()
    return None

@router.post("/{id}/comments", status_code=status.HTTP_201_CREATED)
def add_comment(id: int, data: ComentarioCreate, session: SessionDep, current_user: Usuario = Depends(get_current_user)):
    video = session.get(Video, id)
    if not video:
        raise HTTPException(status_code=404, detail="Video no encontrado")
    
    comentario = Comentario(content=data.content, user_id=current_user.id, video_id=id)
    session.add(comentario)
    session.commit()
    session.refresh(comentario)
    return comentario

@router.get("/{id}/comments")
def get_comments(id: int, session: SessionDep):
    return session.exec(select(Comentario).where(Comentario.video_id == id).order_by(Comentario.id.desc())).all()