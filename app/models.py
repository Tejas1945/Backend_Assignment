from pydantic import BaseModel, Field
from typing import List, Optional

class Offer(BaseModel):
    name: str
    value_props: List[str]
    ideal_use_cases: List[str]

class Lead(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    company: Optional[str] = None
    industry: Optional[str] = None
    location: Optional[str] = None
    linkedin_bio: Optional[str] = None

class LeadScore(Lead):
    intent: str
    score: int
    reasoning: str
