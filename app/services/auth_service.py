import bcrypt
from fastapi import HTTPException, status
from app.models.user import User
from app.repositories.user_repo import UserRepository

class AuthService:

    @staticmethod
    def hash_password(password: str) -> str:
        # Generate salt and hash the password
        pwd_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(pwd_bytes, salt)
        return hashed.decode('utf-8')

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        # Check plain password against stored hash
        return bcrypt.checkpw(
            plain_password.encode('utf-8'), 
            hashed_password.encode('utf-8')
        )

    @staticmethod
    def register_user(db, data):
    
        existing_user = UserRepository.get_by_email(db, data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered"
            )

    
        # Replaced pwd_context.hash with direct bcrypt hashing
        hashed_password = AuthService.hash_password(data.password)

        
        new_user = User(
            email=data.email,
            password_hash=hashed_password,   
            display_name=data.display_name,
            account_type=data.account_type or "listener"
        )

    
        UserRepository.create(db, new_user)

        
        return {
            "success": True,
            "message": "Registration successful. Please check your email to verify your account.",
            "data": {
                "user_id": str(new_user.user_id),
                "email": new_user.email,
                "display_name": new_user.display_name,
                "is_verified": new_user.is_verified
            }
        }