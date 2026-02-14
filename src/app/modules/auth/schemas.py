from pydantic import BaseModel, Field

class RegisterIn(BaseModel):
    email: str
    password: str

class LoginIn(BaseModel):
    email: str
    password: str

class TokenPairOut(BaseModel):
    access_token: str
    refresh_token: str

class RefreshIn(BaseModel):
    refresh_token: str

class LogoutIn(BaseModel):
    refresh_token: str

class SendVerificationIn(BaseModel):
    email: str

class VerifyEmailIn(BaseModel):
    email: str
    otp: str = Field(min_length=4, max_length=12)

class ForgotPasswordIn(BaseModel):
    email: str

class ResetPasswordIn(BaseModel):
    email: str
    token: str
    new_password: str
