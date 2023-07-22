from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel


class Attachment(BaseModel):
    id: Optional[int] = None
    ts: Optional[int] = None
    fallback: Optional[str] = None
    text: Optional[str] = None
    title: str
    author_name: Optional[str] = None
    author_link: Optional[str] = None


class SlackMessage(BaseModel):
    type: Optional[str] = None
    subtype: Optional[str] = None
    text: Optional[str] = None
    ts: Optional[str] = None
    bot_id: Optional[str] = None
    blocks: Optional[List[dict]] = None
    attachments: Optional[List[Attachment]] = None
