from pydantic import BaseModel

class SignupIn(BaseModel):
    email: str
    password: str

class LoginIn(BaseModel):
    email: str
    password: str

class TokenOut(BaseModel):
    token: str

class PublicUserOut(BaseModel):
    id: str
    email: str
    is_beta_approved: bool
    is_email_verified: bool
