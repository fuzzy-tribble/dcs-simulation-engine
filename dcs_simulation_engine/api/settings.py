"""Runtime configuration for the API.

Uses Pydantic BaseSettings to read environment variables with the
`DCS_API_` prefix.

Example:
    export DCS_API_CORS_ALLOW_ALL=false
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings read from environment variables.

    Attributes:
        cors_allow_all (bool): Whether to allow all CORS origins. Useful in dev.
    """

    cors_allow_all: bool = True

    class Config:
        """Pydantic config for environment variable prefix."""

        env_prefix = "DCS_API_"


# Notes/Assumptions:
# - Keep this minimal. Add database URLs, auth providers, etc., as needed.
settings = Settings()
