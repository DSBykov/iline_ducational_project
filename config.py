import os
import secrets


class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', secrets.token_hex(16)) # os.getenv('SECRET_KEY') or 'bd_password'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        f'postgresql://postgres:{SECRET_KEY}@localhost:5432/iline_db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

