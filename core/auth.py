from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pymongo import MongoClient
from bson import ObjectId
from typing import Optional
import os
from dotenv import dotenv_values

# Reusable components
# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

class AuthService:
    def __init__(self):
        config = dotenv_values(".env")
        self.client = MongoClient(config.get("ATLAS_URI"))
        self.db = self.client[config.get("DB_NAME")]
        self.secret_key = config.get("TOKEN_KEY")
        self.algorithm = config.get("ALGORITHM")

    async def get_current_user_id(self, token: str = Depends(oauth2_scheme)) -> ObjectId:
        """Centralized user ID resolver"""
        credentials_exception = HTTPException(
            status_code=401,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            email: str = payload.get("sub")
            if not email:
                raise credentials_exception
                
            user = self.db.users.find_one({"email": email})
            if not user:
                raise credentials_exception
                
            return user["_id"]  # Returns ObjectId
            
        except JWTError:
            raise credentials_exception

# Singleton instance
auth_service = AuthService()