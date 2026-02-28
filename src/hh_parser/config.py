import os
from dotenv import load_dotenv

from pydantic_settings import BaseSettings

load_dotenv()

class Setting(BaseSettings):
    token_hh: str = os.getenv("TOKEN_HH", "")
    name_app: str = os.getenv("NAME_APP", "")
    email: str = os.getenv("EMAIL", "")

settings = Setting()