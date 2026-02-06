from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship
from uuid import UUID, uuid4
import time
from sqlalchemy import BigInteger

def get_current_timestamp():
    return int(time.time() * 1000)

class Room(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    roomId: str = Field(index=True, unique=True) # Public Room Code
    roomName: str
    version: int = Field(default=0)
    
    # Auth Tokens
    adminToken: str = Field(default_factory=lambda: str(uuid4()))
    joinToken: str = Field(default_factory=lambda: str(uuid4()))

    createdAt: int = Field(default_factory=get_current_timestamp, sa_type=BigInteger)
    updatedAt: int = Field(default_factory=get_current_timestamp, sa_type=BigInteger)

    # Relationships
    items: List["TodoItem"] = Relationship(back_populates="room", sa_relationship_kwargs={"cascade": "all, delete"})

# API Models
class RoomCreate(SQLModel):
    roomName: str = "New Room"
    roomId: Optional[str] = None # Optional custom ID


class TodoItem(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    text: str
    done: bool = Field(default=False)
    doneBy: Optional[str] = None
    priority: Optional[str] = Field(default="medium", sa_column_kwargs={"nullable": True})  # Temporarily nullable
    createdAt: int = Field(default_factory=get_current_timestamp, sa_type=BigInteger)
    updatedAt: int = Field(default_factory=get_current_timestamp, sa_type=BigInteger)

    # Foreign Key
    room_db_id: str = Field(foreign_key="room.id")
    room: Room = Relationship(back_populates="items")
