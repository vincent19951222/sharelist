import time
from typing import Optional
from uuid import uuid4

from sqlalchemy import BigInteger, UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel


def get_current_timestamp() -> int:
    return int(time.time() * 1000)


class Room(SQLModel, table=True):
    __tablename__ = "rooms"

    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    room_code: str = Field(index=True, unique=True)
    title: str
    timezone: str = Field(default="Asia/Shanghai")
    is_seeded: bool = Field(default=False)
    never_expires: bool = Field(default=False)
    created_at: int = Field(default_factory=get_current_timestamp, sa_type=BigInteger)
    updated_at: int = Field(default_factory=get_current_timestamp, sa_type=BigInteger)
    last_activity_at: int = Field(default_factory=get_current_timestamp, sa_type=BigInteger)

    members: list["RoomMember"] = Relationship(
        back_populates="room",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    items: list["TodoItem"] = Relationship(
        back_populates="room",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    auto_quests: list["AutoQuest"] = Relationship(
        back_populates="room",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    gp_ledger_entries: list["GpLedger"] = Relationship(
        back_populates="room",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    name: str = Field(index=True, unique=True)
    display_name: str
    avatar_url: str
    created_at: int = Field(default_factory=get_current_timestamp, sa_type=BigInteger)
    updated_at: int = Field(default_factory=get_current_timestamp, sa_type=BigInteger)

    memberships: list["RoomMember"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    created_items: list["TodoItem"] = Relationship(
        back_populates="created_by_user",
        sa_relationship_kwargs={"foreign_keys": "[TodoItem.created_by_user_id]"},
    )
    completed_items: list["TodoItem"] = Relationship(
        back_populates="completed_by_user",
        sa_relationship_kwargs={"foreign_keys": "[TodoItem.completed_by_user_id]"},
    )
    created_auto_quests: list["AutoQuest"] = Relationship(back_populates="created_by_user")
    gp_ledger_entries: list["GpLedger"] = Relationship(back_populates="user")


class RoomMember(SQLModel, table=True):
    __tablename__ = "room_members"
    __table_args__ = (UniqueConstraint("room_id", "user_id", name="uq_room_members_room_user"),)

    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    room_id: str = Field(foreign_key="rooms.id", index=True)
    user_id: str = Field(foreign_key="users.id", index=True)
    role: str = Field(default="admin")
    created_at: int = Field(default_factory=get_current_timestamp, sa_type=BigInteger)

    room: Room = Relationship(back_populates="members")
    user: User = Relationship(back_populates="memberships")


class AutoQuest(SQLModel, table=True):
    __tablename__ = "auto_quests"

    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    room_id: str = Field(foreign_key="rooms.id", index=True)
    title: str
    reward_gp: int = Field(default=10)
    repeat_mask: int = Field(default=0)
    is_enabled: bool = Field(default=True)
    created_by_user_id: str = Field(foreign_key="users.id", index=True)
    created_at: int = Field(default_factory=get_current_timestamp, sa_type=BigInteger)
    updated_at: int = Field(default_factory=get_current_timestamp, sa_type=BigInteger)

    room: Room = Relationship(back_populates="auto_quests")
    created_by_user: User = Relationship(back_populates="created_auto_quests")
    items: list["TodoItem"] = Relationship(back_populates="auto_quest")


class TodoItem(SQLModel, table=True):
    __tablename__ = "todo_items"
    __table_args__ = (UniqueConstraint("auto_quest_id", "scheduled_date", name="uq_todo_auto_quest_schedule"),)

    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    room_id: str = Field(foreign_key="rooms.id", index=True)
    title: str
    done: bool = Field(default=False)
    is_deleted: bool = Field(default=False)
    reward_gp: int = Field(default=10)
    source_type: str = Field(default="manual")
    auto_quest_id: Optional[str] = Field(default=None, foreign_key="auto_quests.id", index=True)
    scheduled_date: Optional[str] = Field(default=None, index=True)
    created_by_user_id: str = Field(foreign_key="users.id", index=True)
    completed_by_user_id: Optional[str] = Field(default=None, foreign_key="users.id", index=True)
    completed_at: Optional[int] = Field(default=None, sa_type=BigInteger)
    created_at: int = Field(default_factory=get_current_timestamp, sa_type=BigInteger)
    updated_at: int = Field(default_factory=get_current_timestamp, sa_type=BigInteger)

    room: Room = Relationship(back_populates="items")
    auto_quest: Optional[AutoQuest] = Relationship(back_populates="items")
    created_by_user: User = Relationship(
        back_populates="created_items",
        sa_relationship_kwargs={"foreign_keys": "[TodoItem.created_by_user_id]"},
    )
    completed_by_user: Optional[User] = Relationship(
        back_populates="completed_items",
        sa_relationship_kwargs={"foreign_keys": "[TodoItem.completed_by_user_id]"},
    )


class GpLedger(SQLModel, table=True):
    __tablename__ = "gp_ledger"

    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    room_id: str = Field(foreign_key="rooms.id", index=True)
    user_id: str = Field(foreign_key="users.id", index=True)
    todo_item_id: str = Field(index=True)
    todo_title: str
    gp_delta: int
    source_type: str = Field(default="todo_completion")
    awarded_at: int = Field(default_factory=get_current_timestamp, sa_type=BigInteger)
    reversed_at: Optional[int] = Field(default=None, sa_type=BigInteger)

    room: Room = Relationship(back_populates="gp_ledger_entries")
    user: User = Relationship(back_populates="gp_ledger_entries")
