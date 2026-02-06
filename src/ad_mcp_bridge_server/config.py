"""Configuration settings for MCP Bridge Server"""
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    """
    Settings for connecting to Odoo and running the MCP server.
    Environment variables: ODOO_URL, ODOO_DB, ODOO_API_KEY, etc.
    """
    
    # Odoo connection
    url: str = Field(
        default="http://localhost:8069",
        description="Odoo server URL",
        alias="ODOO_URL"
    )
    db: Optional[str] = Field(
        default=None,
        description="Odoo database name",
        alias="ODOO_DB"
    )
    
    # Authentication - API key preferred
    api_key: Optional[str] = Field(
        default=None,
        description="API key from Odoo MCP Bridge module",
        alias="ODOO_API_KEY"
    )
    
    # Alternative authentication - username/password
    user: Optional[str] = Field(
        default=None,
        description="Odoo username (if not using API key)",
        alias="ODOO_USER"
    )
    password: Optional[str] = Field(
        default=None,
        description="Odoo password (if not using API key)",
        alias="ODOO_PASSWORD"
    )
    
    # MCP transport settings
    mcp_transport: str = Field(
        default="stdio",
        description="MCP transport: stdio or streamable-http"
    )
    mcp_host: str = Field(
        default="localhost",
        description="Host for HTTP transport"
    )
    mcp_port: int = Field(
        default=8000,
        description="Port for HTTP transport"
    )
    
    # Behavior settings
    max_records: int = Field(
        default=100,
        description="Default max records per query",
        alias="ODOO_MAX_RECORDS"
    )
    timeout: int = Field(
        default=30,
        description="Request timeout in seconds",
        alias="ODOO_TIMEOUT"
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"
        populate_by_name = True
    
    @property
    def has_api_key(self) -> bool:
        return bool(self.api_key)
    
    @property
    def has_credentials(self) -> bool:
        return bool(self.user and self.password)
    
    @property
    def can_connect(self) -> bool:
        return self.has_api_key or self.has_credentials


# Global settings instance
settings = Settings()
