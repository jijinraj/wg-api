from pydantic import BaseModel

class MeOut(BaseModel):
    id: str
    email: str
    role: str
    is_beta_approved: bool
    is_email_verified: bool
    created_at: str
