
import pytest

from aegis.auth import (
    AuthenticationManager,
    User,
    UserRole,
)


@pytest.fixture
def auth_manager():
    """Create a fresh authentication manager for each test."""
    return AuthenticationManager()


class TestAuthenticationManager:
    """Tests for AuthenticationManager."""

    def test_create_user(self, auth_manager):
        """Test creating a new user."""
        user = auth_manager.create_user(
            username="testuser",
            email="test@example.com",
            role=UserRole.CLINICIAN,
        )

        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.role == UserRole.CLINICIAN
        assert user.is_active is True
        assert user.user_id in auth_manager.users

    def test_get_user(self, auth_manager):
        """Test getting a user by ID."""
        user = auth_manager.create_user(
            username="testuser",
            email="test@example.com",
        )

        retrieved = auth_manager.get_user(user.user_id)
        assert retrieved is not None
        assert retrieved.username == "testuser"

    def test_get_user_not_found(self, auth_manager):
        """Test getting a non-existent user."""
        retrieved = auth_manager.get_user("nonexistent")
        assert retrieved is None

    def test_get_user_by_username(self, auth_manager):
        """Test getting a user by username."""
        auth_manager.create_user(
            username="testuser",
            email="test@example.com",
        )

        retrieved = auth_manager.get_user_by_username("testuser")
        assert retrieved is not None
        assert retrieved.email == "test@example.com"

    def test_get_user_by_username_not_found(self, auth_manager):
        """Test getting a non-existent user by username."""
        retrieved = auth_manager.get_user_by_username("nonexistent")
        assert retrieved is None

    def test_create_api_key(self, auth_manager):
        """Test creating an API key."""
        user = auth_manager.create_user(
            username="testuser",
            email="test@example.com",
        )

        raw_key, api_key = auth_manager.create_api_key(
            user_id=user.user_id,
            name="Test Key",
            scopes=["read", "write"],
        )

        assert raw_key.startswith("aegis_")
        assert api_key.user_id == user.user_id
        assert api_key.name == "Test Key"
        assert api_key.scopes == ["read", "write"]
        assert api_key.is_active is True

    def test_validate_api_key(self, auth_manager):
        """Test validating an API key."""
        user = auth_manager.create_user(
            username="testuser",
            email="test@example.com",
        )

        raw_key, _ = auth_manager.create_api_key(
            user_id=user.user_id,
            name="Test Key",
        )

        validated_user = auth_manager.validate_api_key(raw_key)
        assert validated_user is not None
        assert validated_user.user_id == user.user_id

    def test_validate_api_key_invalid(self, auth_manager):
        """Test validating an invalid API key."""
        validated_user = auth_manager.validate_api_key("invalid_key")
        assert validated_user is None

    def test_validate_api_key_inactive(self, auth_manager):
        """Test validating an inactive API key."""
        user = auth_manager.create_user(
            username="testuser",
            email="test@example.com",
        )

        raw_key, api_key = auth_manager.create_api_key(
            user_id=user.user_id,
            name="Test Key",
        )

        # Deactivate the key
        api_key.is_active = False

        validated_user = auth_manager.validate_api_key(raw_key)
        assert validated_user is None

    def test_create_session(self, auth_manager):
        """Test creating a session."""
        user = auth_manager.create_user(
            username="testuser",
            email="test@example.com",
        )

        session = auth_manager.create_session(
            user_id=user.user_id,
            ip_address="127.0.0.1",
            user_agent="test-agent",
        )

        assert session.user_id == user.user_id
        assert session.ip_address == "127.0.0.1"
        assert session.user_agent == "test-agent"
        assert session.session_id in auth_manager.sessions

    def test_validate_session(self, auth_manager):
        """Test validating a session."""
        user = auth_manager.create_user(
            username="testuser",
            email="test@example.com",
        )

        session = auth_manager.create_session(user_id=user.user_id)

        validated_user = auth_manager.validate_session(session.session_id)
        assert validated_user is not None
        assert validated_user.user_id == user.user_id

    def test_validate_session_not_found(self, auth_manager):
        """Test validating a non-existent session."""
        validated_user = auth_manager.validate_session("nonexistent")
        assert validated_user is None

    def test_check_permission(self, auth_manager):
        """Test role-based permission checking."""
        admin = User(
            user_id="admin",
            username="admin",
            email="admin@example.com",
            role=UserRole.ADMIN,
        )

        clinician = User(
            user_id="clinician",
            username="clinician",
            email="clinician@example.com",
            role=UserRole.CLINICIAN,
        )

        viewer = User(
            user_id="viewer",
            username="viewer",
            email="viewer@example.com",
            role=UserRole.VIEWER,
        )

        # Admin can access everything
        assert auth_manager.check_permission(admin, UserRole.ADMIN) is True
        assert auth_manager.check_permission(admin, UserRole.CLINICIAN) is True
        assert auth_manager.check_permission(admin, UserRole.VIEWER) is True

        # Clinician can access clinician and viewer
        assert auth_manager.check_permission(clinician, UserRole.ADMIN) is False
        assert auth_manager.check_permission(clinician, UserRole.CLINICIAN) is True
        assert auth_manager.check_permission(clinician, UserRole.VIEWER) is True

        # Viewer can only access viewer
        assert auth_manager.check_permission(viewer, UserRole.ADMIN) is False
        assert auth_manager.check_permission(viewer, UserRole.CLINICIAN) is False
        assert auth_manager.check_permission(viewer, UserRole.VIEWER) is True
