"""
modules/user/schemas.py — defines the JSON formats for user signup/login requests and responses.

request/response models for the user API.

These Pydantic models define the JSON structure for user endpoints:
- SignupIn: expected request body for /user/signup (email + password).
- LoginIn: expected request body for /user/login (email + password).
- TokenOut: response body for /user/login (JWT token).
- PublicUserOut: safe public user response (no sensitive fields like password_hash).

FastAPI uses these to validate input, serialize output, and generate API docs.
"""

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
