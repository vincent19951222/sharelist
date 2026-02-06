"""
Unit tests for priority validation
"""

import pytest
from backend.main import validate_priority


class TestPriorityValidation:
    """Test priority validation function"""

    def test_valid_high_priority(self):
        """Should accept 'high' priority"""
        assert validate_priority("high") == "high"

    def test_valid_medium_priority(self):
        """Should accept 'medium' priority"""
        assert validate_priority("medium") == "medium"

    def test_valid_low_priority(self):
        """Should accept 'low' priority"""
        assert validate_priority("low") == "low"

    def test_none_defaults_to_medium(self):
        """Should default to 'medium' when None"""
        assert validate_priority(None) == "medium"

    def test_invalid_priority_raises_error(self):
        """Should raise ValueError for invalid priority"""
        with pytest.raises(ValueError, match="Invalid priority"):
            validate_priority("urgent")

        with pytest.raises(ValueError, match="Invalid priority"):
            validate_priority("HIGH")  # Case-sensitive

        with pytest.raises(ValueError, match="Invalid priority"):
            validate_priority("")

        with pytest.raises(ValueError, match="Invalid priority"):
            validate_priority("invalid")
