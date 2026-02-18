"""TestUsers — test user emails loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class TestUsers:
    """Test user emails for admin/project operations."""

    user: str = "user@company.com"
    user_new: str = "newuser@company.com"
    user_departing: str = "departing@company.com"
    user_admin: str = "admin1@co.com"
    user_csv: str = "user1@co.com"
    user_add: str = "new.user@company.com"
    user_pm: str = "pm@company.com"
    user_struct: str = "struct@co.com"
    user_mep: str = "mep@co.com"
    user_folder: str = "user@co.com"
    user_old_admin: str = "admin@old.com"

    @classmethod
    def from_env(cls) -> TestUsers:
        """Load test user emails from environment variables with defaults."""
        return cls(
            user=os.environ.get("TEST_USER", cls.user),
            user_new=os.environ.get("TEST_USER_NEW", cls.user_new),
            user_departing=os.environ.get("TEST_USER_DEPARTING", cls.user_departing),
            user_admin=os.environ.get("TEST_USER_ADMIN", cls.user_admin),
            user_csv=os.environ.get("TEST_USER_CSV", cls.user_csv),
            user_add=os.environ.get("TEST_USER_ADD", cls.user_add),
            user_pm=os.environ.get("TEST_USER_PM", cls.user_pm),
            user_struct=os.environ.get("TEST_USER_STRUCT", cls.user_struct),
            user_mep=os.environ.get("TEST_USER_MEP", cls.user_mep),
            user_folder=os.environ.get("TEST_USER_FOLDER", cls.user_folder),
            user_old_admin=os.environ.get("TEST_USER_OLD_ADMIN", cls.user_old_admin),
        )
