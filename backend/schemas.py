from typing import Optional

from pydantic import BaseModel


class ComplaintIn(BaseModel):
    name: str
    phone: Optional[str] = ""
    location: str
    category: str
    description: str
    photo_b64: Optional[str] = ""
