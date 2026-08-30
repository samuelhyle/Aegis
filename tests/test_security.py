import pytest

from aegis.security import (
    AuditEvent,
    AuditEventType,
    AuditLogger,
    AuditSeverity,
    InputSanitizer,
    SecretsManager,
    SecurityHeaders,
)


@pytest.fixture
def audit_logger():
    """Create an audit logger for testing."""
    return AuditLogger()


@pytest.fixture
def secrets_manager():
    """Create a secrets manager for testing."""
    return SecretsManager()


class TestAuditLogger:
    """Tests for AuditLogger."""

    def test_log_event(self, audit_logger):
        """Test logging an audit event."""
        event = AuditEvent(
            event_type=AuditEventType.AUTH_SUCCESS,
            user_id="test-user",
            action="login",
        )
        audit_logger.log(event)
        assert len(audit_logger.events) == 1
        assert audit_logger.events[0].user_id == "test-user"

    def test_log_auth_success(self, audit_logger):
        """Test logging auth success."""
        audit_logger.log_auth_success("user1", "127.0.0.1", "api_key")
        assert len(audit_logger.events) == 1
        assert audit_logger.events[0].event_type == AuditEventType.AUTH_SUCCESS

    def test_log_auth_failure(self, audit_logger):
        """Test logging auth failure."""
        audit_logger.log_auth_failure("127.0.0.1", "invalid_key", "testuser")
        assert len(audit_logger.events) == 1
        assert audit_logger.events[0].event_type == AuditEventType.AUTH_FAILURE
        assert audit_logger.events[0].severity == AuditSeverity.WARNING

    def test_log_data_access(self, audit_logger):
        """Test logging data access."""
        audit_logger.log_data_access("user1", "patient", "123")
        assert len(audit_logger.events) == 1
        assert audit_logger.events[0].event_type == AuditEventType.DATA_ACCESS

    def test_log_investigation(self, audit_logger):
        """Test logging investigation."""
        audit_logger.log_investigation("user1", "patient123", "test question", "trace123")
        assert len(audit_logger.events) == 1
        assert audit_logger.events[0].event_type == AuditEventType.INVESTIGATION

    def test_log_security_event(self, audit_logger):
        """Test logging security event."""
        audit_logger.log_security_event("suspicious_activity", "user1", "127.0.0.1")
        assert len(audit_logger.events) == 1
        assert audit_logger.events[0].event_type == AuditEventType.SECURITY_EVENT

    def test_get_events(self, audit_logger):
        """Test getting events."""
        audit_logger.log_auth_success("user1", "127.0.0.1", "api_key")
        audit_logger.log_auth_failure("127.0.0.1", "invalid_key")

        events = audit_logger.get_events()
        assert len(events) == 2

    def test_get_events_filtered(self, audit_logger):
        """Test getting filtered events."""
        audit_logger.log_auth_success("user1", "127.0.0.1", "api_key")
        audit_logger.log_auth_failure("127.0.0.1", "invalid_key")

        events = audit_logger.get_events(event_type=AuditEventType.AUTH_SUCCESS)
        assert len(events) == 1

    def test_get_security_events(self, audit_logger):
        """Test getting security events."""
        audit_logger.log_auth_success("user1", "127.0.0.1", "api_key")
        audit_logger.log_auth_failure("127.0.0.1", "invalid_key")
        audit_logger.log_security_event("test", "user1", "127.0.0.1")

        events = audit_logger.get_security_events()
        assert len(events) == 2  # auth_failure + security_event


class TestInputSanitizer:
    """Tests for InputSanitizer."""

    def test_sanitize_string(self):
        """Test string sanitization."""
        result = InputSanitizer.sanitize_string("  hello world  ")
        assert result == "hello world"

    def test_sanitize_string_max_length(self):
        """Test string sanitization with max length."""
        result = InputSanitizer.sanitize_string("a" * 2000, max_length=100)
        assert len(result) == 100

    def test_sanitize_string_null_bytes(self):
        """Test null byte removal."""
        result = InputSanitizer.sanitize_string("hello\x00world")
        assert result == "helloworld"

    def test_check_sql_injection(self):
        """Test SQL injection detection."""
        assert InputSanitizer.check_sql_injection("SELECT * FROM users") is True
        assert InputSanitizer.check_sql_injection("normal text") is False
        assert InputSanitizer.check_sql_injection("1 OR 1=1") is True

    def test_check_xss(self):
        """Test XSS detection."""
        assert InputSanitizer.check_xss("<script>alert('xss')</script>") is True
        assert InputSanitizer.check_xss("normal text") is False
        assert InputSanitizer.check_xss("javascript:alert(1)") is True

    def test_check_path_traversal(self):
        """Test path traversal detection."""
        assert InputSanitizer.check_path_traversal("../../../etc/passwd") is True
        assert InputSanitizer.check_path_traversal("normal/path") is False

    def test_validate_input(self):
        """Test input validation."""
        result = InputSanitizer.validate_input("normal text")
        assert result == "normal text"

    def test_validate_input_sql_injection(self):
        """Test input validation with SQL injection."""
        with pytest.raises(ValueError, match="SQL injection"):
            InputSanitizer.validate_input("SELECT * FROM users")

    def test_validate_patient_id(self):
        """Test patient ID validation."""
        result = InputSanitizer.validate_patient_id("patient-123")
        assert result == "patient-123"

    def test_validate_patient_id_invalid(self):
        """Test invalid patient ID."""
        with pytest.raises(ValueError, match="Invalid patient ID"):
            InputSanitizer.validate_patient_id("patient@123")

    def test_validate_question(self):
        """Test question validation."""
        result = InputSanitizer.validate_question("What is the patient's condition?")
        assert result == "What is the patient's condition?"

    def test_validate_question_too_short(self):
        """Test question too short."""
        with pytest.raises(ValueError, match="too short"):
            InputSanitizer.validate_question("ab")


class TestSecretsManager:
    """Tests for SecretsManager."""

    def test_get_default(self, secrets_manager):
        """Test getting default value."""
        result = secrets_manager.get("NONEXISTENT", "default")
        assert result == "default"

    def test_set_and_get(self, secrets_manager):
        """Test setting and getting secret."""
        secrets_manager.set("TEST_SECRET", "my-secret")
        result = secrets_manager.get("TEST_SECRET")
        assert result == "my-secret"

    def test_get_masked(self, secrets_manager):
        """Test getting masked secret."""
        secrets_manager.set("TEST_SECRET", "abcdefghijklmnop")
        result = secrets_manager.get_masked("TEST_SECRET")
        assert result == "ab...op"

    def test_get_masked_short(self, secrets_manager):
        """Test getting masked short secret."""
        secrets_manager.set("TEST_SECRET", "abc")
        result = secrets_manager.get_masked("TEST_SECRET")
        assert result == "****"

    def test_rotate(self, secrets_manager):
        """Test rotating secret."""
        old_value = secrets_manager.get("TEST_SECRET", "")
        new_value = secrets_manager.rotate("TEST_SECRET")
        assert new_value != old_value
        assert len(new_value) > 0


class TestSecurityHeaders:
    """Tests for SecurityHeaders."""

    def test_get_headers(self):
        """Test getting security headers."""
        headers = SecurityHeaders.get_headers()
        assert "X-Content-Type-Options" in headers
        assert "X-Frame-Options" in headers
        assert "X-XSS-Protection" in headers
        assert "Strict-Transport-Security" in headers
        assert "Content-Security-Policy" in headers
