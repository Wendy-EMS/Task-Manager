from pydantic import BaseModel, Field, field_validator


class Credentials(BaseModel):
    email: str
    password: str = Field(min_length=8)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        email = value.strip().lower()
        if " " in email or email.count("@") != 1:
            raise ValueError("Email invalide")
        local, domain = email.split("@")
        if not local or "." not in domain:
            raise ValueError("Email invalide")
        return email

    @field_validator("password")
    @classmethod
    def password_fits_bcrypt(cls, value: str) -> str:
        if len(value.encode("utf-8")) > 72:
            raise ValueError("Le mot de passe dépasse 72 octets")
        return value


class UserRead(BaseModel):
    id: int
    email: str


class Token(BaseModel):
    access_token: str
    token_type: str
