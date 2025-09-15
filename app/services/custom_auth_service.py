from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import JWTError, jwt
from supabase import create_client, Client
import logging
import secrets
from app.config import settings

class CustomAuthService:
    """
    Custom Username/Password Authentication Service
    Uses Supabase database for user storage with JWT token management
    """
    
    def __init__(self):
        self.supabase: Client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_SERVICE_KEY
        )
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.logger = logging.getLogger(__name__)
        
        # JWT Settings
        self.secret_key = settings.JWT_SECRET_KEY
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 30
        self.refresh_token_expire_days = 7
    
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        return self.pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    async def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Authenticate user with username/password
        """
        try:
            # Get user from database
            result = self.supabase.table('users') \
                .select('*') \
                .eq('username', username) \
                .eq('is_active', True) \
                .execute()
            
            if not result.data:
                self.logger.warning(f"User not found: {username}")
                return None
            
            user = result.data[0]
            
            # Verify password
            if not self.verify_password(password, user['password_hash']):
                self.logger.warning(f"Invalid password for user: {username}")
                return None
            
            # Update last login
            self.supabase.table('users') \
                .update({'last_login': datetime.now().isoformat()}) \
                .eq('id', user['id']) \
                .execute()
            
            self.logger.info(f"User authenticated successfully: {username}")
            return user
            
        except Exception as e:
            self.logger.error(f"Authentication error for {username}: {str(e)}")
            return None
    
    def create_access_token(self, user_data: Dict[str, Any]) -> str:
        """Create JWT access token"""
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        to_encode = {
            "sub": str(user_data["id"]),
            "username": user_data["username"],
            "role": user_data["role"],
            "exp": expire,
            "type": "access"
        }
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
    
    def create_refresh_token(self, user_data: Dict[str, Any]) -> str:
        """Create JWT refresh token"""
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        to_encode = {
            "sub": str(user_data["id"]),
            "username": user_data["username"],
            "exp": expire,
            "type": "refresh"
        }
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
    
    async def create_session(self, user: Dict[str, Any], ip_address: str = None, user_agent: str = None) -> Dict[str, Any]:
        """Create user session with tokens"""
        try:
            access_token = self.create_access_token(user)
            refresh_token = self.create_refresh_token(user)
            
            # Generate unique session token
            session_token = secrets.token_urlsafe(32)
            
            # Store session in database
            session_data = {
                "user_id": user["id"],
                "session_token": session_token,
                "refresh_token": refresh_token,
                "expires_at": (datetime.now() + timedelta(days=self.refresh_token_expire_days)).isoformat(),
                "ip_address": ip_address,
                "user_agent": user_agent
            }
            
            session_result = self.supabase.table('user_sessions').insert(session_data).execute()
            
            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "session_token": session_token,
                "token_type": "bearer",
                "expires_in": self.access_token_expire_minutes * 60,
                "user": {
                    "id": user["id"],
                    "username": user["username"],
                    "full_name": user["full_name"],
                    "role": user["role"]
                }
            }
            
        except Exception as e:
            self.logger.error(f"Session creation error: {str(e)}")
            raise
    
    async def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token and return user data"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            user_id = payload.get("sub")
            
            if user_id is None:
                return None
            
            # Get user from database
            result = self.supabase.table('users') \
                .select('*') \
                .eq('id', int(user_id)) \
                .eq('is_active', True) \
                .execute()
            
            if not result.data:
                return None
            
            user = result.data[0]
            user['token_data'] = payload
            return user
            
        except JWTError as e:
            self.logger.warning(f"Token verification failed: {str(e)}")
            return None
        except Exception as e:
            self.logger.error(f"Token verification error: {str(e)}")
            return None
    
    async def refresh_access_token(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        """Refresh access token using refresh token"""
        try:
            payload = jwt.decode(refresh_token, self.secret_key, algorithms=[self.algorithm])
            
            if payload.get("type") != "refresh":
                return None
            
            user_id = payload.get("sub")
            
            # Verify session exists
            session_result = self.supabase.table('user_sessions') \
                .select('*') \
                .eq('refresh_token', refresh_token) \
                .eq('user_id', int(user_id)) \
                .gte('expires_at', datetime.now().isoformat()) \
                .execute()
            
            if not session_result.data:
                return None
            
            # Get user data
            user_result = self.supabase.table('users') \
                .select('*') \
                .eq('id', int(user_id)) \
                .eq('is_active', True) \
                .execute()
            
            if not user_result.data:
                return None
            
            user = user_result.data[0]
            new_access_token = self.create_access_token(user)
            
            # Update session last_used
            self.supabase.table('user_sessions') \
                .update({'last_used': datetime.now().isoformat()}) \
                .eq('refresh_token', refresh_token) \
                .execute()
            
            return {
                "access_token": new_access_token,
                "token_type": "bearer",
                "expires_in": self.access_token_expire_minutes * 60
            }
            
        except JWTError:
            return None
        except Exception as e:
            self.logger.error(f"Token refresh error: {str(e)}")
            return None
    
    async def logout(self, session_token: str) -> bool:
        """Logout user by removing session"""
        try:
            result = self.supabase.table('user_sessions') \
                .delete() \
                .eq('session_token', session_token) \
                .execute()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Logout error: {str(e)}")
            return False
    
    async def create_user(self, username: str, password: str, full_name: str, role: str = "user") -> Optional[Dict[str, Any]]:
        """Create new user (admin only)"""
        try:
            password_hash = self.hash_password(password)
            
            user_data = {
                "username": username,
                "password_hash": password_hash,
                "full_name": full_name,
                "role": role,
                "is_active": True
            }
            
            result = self.supabase.table('users').insert(user_data).execute()
            
            if result.data:
                created_user = result.data[0]
                # Remove password hash from response
                created_user.pop('password_hash', None)
                return created_user
            
            return None
            
        except Exception as e:
            self.logger.error(f"User creation error: {str(e)}")
            return None