from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any
from uuid import uuid4

from fastapi import Depends, HTTPException, Request, Security
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer


class UserRole(StrEnum):
    """User roles for RBAC."""
    ADMIN = "admin"
    CLINICIAN = "clinician"
    RESEARCHER = "researcher"
    VIEWER = "viewer"


@dataclass
class User:
    """User model."""
    user_id: str
    username: str
    email: str
    role: UserRole
    is_active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_login: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class APIKey:
    """API key model."""
    key_id: str
    key_hash: str
    user_id: str
    name: str
    is_active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime | None = None
    last_used: datetime | None = None
    scopes: list[str] = field(default_factory=list)


@dataclass
class Session:
    """User session model."""
    session_id: str
    user_id: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    ip_address: str = ""
    user_agent: str = ""


class AuthenticationManager:
    """Manager for authentication and authorization."""

    def __init__(self):
        self.users: dict[str, User] = {}
        self.api_keys: dict[str, APIKey] = {}
        self.sessions: dict[str, Session] = {}
        self._secret_key = os.getenv("AEGIS_SECRET_KEY", os.urandom(32).hex())

    def create_user(
        self,
        username: str,
        email: str,
        role: UserRole = UserRole.VIEWER,
    ) -> User:
        """Create a new user."""
        user_id = str(uuid4())
        user = User(
            user_id=user_id,
            username=username,
            email=email,
            role=role,
        )
        self.users[user_id] = user
        return user

    def get_user(self, user_id: str) -> User | None:
        """Get a user by ID."""
        return self.users.get(user_id)

    def get_user_by_username(self, username: str) -> User | None:
        """Get a user by username."""
        for user in self.users.values():
            if user.username == username:
                return user
        return None

    def create_api_key(
        self,
        user_id: str,
        name: str,
        scopes: list[str] | None = None,
        expires_in_days: int | None = None,
    ) -> tuple[str, APIKey]:
        """Create an API key for a user. Returns (raw_key, api_key_model)."""
        raw_key = f"aegis_{uuid4().hex}"
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

        expires_at = None
        if expires_in_days:
            from datetime import timedelta
            expires_at = datetime.now(timezone.utc) + timedelta(days=expires_in_days)

        api_key = APIKey(
            key_id=str(uuid4()),
            key_hash=key_hash,
            user_id=user_id,
            name=name,
            expires_at=expires_at,
            scopes=scopes or [],
        )
        self.api_keys[api_key.key_id] = api_key
        return raw_key, api_key

    def validate_api_key(self, raw_key: str) -> User | None:
        """Validate an API key and return the associated user."""
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

        for api_key in self.api_keys.values():
            if api_key.key_hash == key_hash and api_key.is_active:
                # Check expiration
                if api_key.expires_at and api_key.expires_at < datetime.now(timezone.utc):
                    continue

                # Update last used
                api_key.last_used = datetime.now(timezone.utc)

                # Get user
                user = self.users.get(api_key.user_id)
                if user and user.is_active:
                    return user

        return None

    def create_session(
        self,
        user_id: str,
        ip_address: str = "",
        user_agent: str = "",
        duration_hours: int = 24,
    ) -> Session:
        """Create a new session for a user."""
        from datetime import timedelta

        session = Session(
            session_id=str(uuid4()),
            user_id=user_id,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=duration_hours),
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self.sessions[session.session_id] = session
        return session

    def validate_session(self, session_id: str) -> User | None:
        """Validate a session and return the associated user."""
        session = self.sessions.get(session_id)
        if not session:
            return None

        if session.expires_at < datetime.now(timezone.utc):
            del self.sessions[session_id]
            return None

        user = self.users.get(session.user_id)
        if user and user.is_active:
            return user

        return None

    def check_permission(self, user: User, required_role: UserRole) -> bool:
        """Check if a user has the required role or higher."""
        role_hierarchy = {
            UserRole.VIEWER: 0,
            UserRole.RESEARCHER: 1,
            UserRole.CLINICIAN: 2,
            UserRole.ADMIN: 3,
        }
        return role_hierarchy.get(user.role, 0) >= role_hierarchy.get(required_role, 0)


# Global auth manager
auth_manager = AuthenticationManager()

# Security schemes
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    api_key: str | None = Security(api_key_header),
    credentials: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
) -> User:
    """Get the current authenticated user from API key or bearer token."""
    # Try API key first
    if api_key:
        user = auth_manager.validate_api_key(api_key)
        if user:
            return user

    # Try bearer token (session ID)
    if credentials and credentials.credentials:
        user = auth_manager.validate_session(credentials.credentials)
        if user:
            return user

    # For development, allow unauthenticated access with default user
    if os.getenv("AEGIS_AUTH_DISABLED", "").lower() == "true":
        default_user = auth_manager.get_user_by_username("default")
        if not default_user:
            default_user = auth_manager.create_user(
                username="default",
                email="default@aegis.local",
                role=UserRole.ADMIN,
            )
        return default_user

    raise HTTPException(
        status_code=401,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "API-Key"},
    )


def require_role(required_role: UserRole):
    """Dependency factory for role-based access control."""
    async def check_role(user: User = Depends(get_current_user)) -> User:
        if not auth_manager.check_permission(user, required_role):
            raise HTTPException(
                status_code=403,
                detail=f"Insufficient permissions. Required role: {required_role.value}",
            )
        return user
    return check_role
