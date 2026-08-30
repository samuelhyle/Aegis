
from aegis.error_handling import ErrorResponse


class TestErrorResponse:
    """Tests for ErrorResponse."""

    def test_create_basic_error(self):
        """Test creating a basic error response."""
        response = ErrorResponse.create(
            status_code=400,
            message="Bad request",
        )

        assert response.status_code == 400
        content = response.body.decode()
        assert "Bad request" in content
        assert "error" in content

    def test_create_error_with_type(self):
        """Test creating an error with custom type."""
        response = ErrorResponse.create(
            status_code=404,
            message="Not found",
            error_type="not_found",
        )

        assert response.status_code == 404
        content = response.body.decode()
        assert "not_found" in content

    def test_create_error_with_details(self):
        """Test creating an error with details."""
        response = ErrorResponse.create(
            status_code=422,
            message="Validation error",
            details={"field": "email", "issue": "invalid format"},
        )

        assert response.status_code == 422
        content = response.body.decode()
        assert "email" in content
        assert "invalid format" in content

    def test_create_error_with_request_id(self):
        """Test creating an error with request ID."""
        response = ErrorResponse.create(
            status_code=500,
            message="Internal error",
            request_id="req-123",
        )

        assert response.status_code == 500
        content = response.body.decode()
        assert "req-123" in content

    def test_create_error_structure(self):
        """Test the structure of error responses."""
        response = ErrorResponse.create(
            status_code=400,
            message="Test error",
            error_type="test_error",
            request_id="test-123",
        )

        import json
        content = json.loads(response.body.decode())

        assert "error" in content
        error = content["error"]
        assert error["type"] == "test_error"
        assert error["message"] == "Test error"
        assert error["request_id"] == "test-123"
        assert "timestamp" in error
