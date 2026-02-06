"""Odoo HTTP client for MCP Bridge Server"""
import json
import httpx
from typing import Any, Optional
from .config import settings


class OdooClient:
    """
    HTTP client for communicating with Odoo MCP Bridge endpoints.
    Uses the HTTP JSON-RPC controllers we created in the Odoo module.
    """
    
    def __init__(
        self,
        url: Optional[str] = None,
        db: Optional[str] = None,
        api_key: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        timeout: int = 30,
    ):
        self.url = (url or settings.url).rstrip('/')
        self.db = db or settings.db
        self.api_key = api_key or settings.api_key
        self.user = user or settings.user
        self.password = password or settings.password
        self.timeout = timeout or settings.timeout
        
        self._client = httpx.AsyncClient(timeout=self.timeout)
    
    async def _request(self, endpoint: str, **params) -> dict:
        """Make a JSON-RPC request to Odoo MCP endpoint"""
        url = f"{self.url}/mcp/{endpoint}"
        
        # Add authentication
        if self.api_key:
            params['api_key'] = self.api_key
        elif self.user and self.password:
            params['user'] = self.user
            params['password'] = self.password
        
        payload = {
            "jsonrpc": "2.0",
            "method": "call",
            "params": params,
            "id": 1,
        }
        
        try:
            response = await self._client.post(
                url,
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            result = response.json()
            
            if "error" in result:
                error = result["error"]
                if isinstance(error, dict):
                    msg = error.get("data", {}).get("message", str(error))
                else:
                    msg = str(error)
                raise OdooError(f"Odoo error: {msg}")
            
            return result.get("result", {})
            
        except httpx.HTTPStatusError as e:
            raise OdooError(f"HTTP error {e.response.status_code}: {e.response.text}")
        except httpx.RequestError as e:
            raise OdooError(f"Connection error: {str(e)}")
    
    async def health_check(self) -> dict:
        """Check Odoo MCP Bridge health"""
        try:
            response = await self._client.get(f"{self.url}/mcp/health")
            return response.json()
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def get_server_info(self) -> dict:
        """Get MCP server information"""
        return await self._request("info")
    
    async def list_models(self) -> list:
        """List enabled models"""
        result = await self._request("models")
        if result.get("error"):
            raise OdooError(result.get("message", "Unknown error"))
        return result.get("data", {}).get("models", [])
    
    async def get_fields(self, model: str) -> list:
        """Get field definitions for a model"""
        result = await self._request("fields", model=model)
        if result.get("error"):
            raise OdooError(result.get("message", "Unknown error"))
        return result.get("data", {}).get("fields", [])
    
    async def search(
        self,
        model: str,
        domain: Optional[list] = None,
        fields: Optional[list] = None,
        limit: int = 80,
        offset: int = 0,
        order: Optional[str] = None,
    ) -> list:
        """Search for records"""
        result = await self._request(
            "search",
            model=model,
            domain=domain or [],
            fields=fields,
            limit=limit,
            offset=offset,
            order=order,
        )
        if result.get("error"):
            raise OdooError(result.get("message", "Unknown error"))
        return result.get("data", {}).get("records", [])
    
    async def read(
        self,
        model: str,
        record_id: int,
        fields: Optional[list] = None,
    ) -> dict:
        """Read a specific record"""
        result = await self._request(
            "read",
            model=model,
            record_id=record_id,
            fields=fields,
        )
        if result.get("error"):
            raise OdooError(result.get("message", "Unknown error"))
        return result.get("data", {}).get("record", {})
    
    async def count(
        self,
        model: str,
        domain: Optional[list] = None,
    ) -> int:
        """Count records matching domain"""
        result = await self._request(
            "count",
            model=model,
            domain=domain or [],
        )
        if result.get("error"):
            raise OdooError(result.get("message", "Unknown error"))
        return result.get("data", {}).get("count", 0)
    
    async def create(
        self,
        model: str,
        values: dict,
    ) -> int:
        """Create a new record"""
        result = await self._request(
            "create",
            model=model,
            values=values,
        )
        if result.get("error"):
            raise OdooError(result.get("message", "Unknown error"))
        return result.get("data", {}).get("id")
    
    async def write(
        self,
        model: str,
        record_id: int,
        values: dict,
    ) -> bool:
        """Update a record"""
        result = await self._request(
            "write",
            model=model,
            record_id=record_id,
            values=values,
        )
        if result.get("error"):
            raise OdooError(result.get("message", "Unknown error"))
        return True
    
    async def unlink(
        self,
        model: str,
        record_id: int,
    ) -> bool:
        """Delete a record"""
        result = await self._request(
            "unlink",
            model=model,
            record_id=record_id,
        )
        if result.get("error"):
            raise OdooError(result.get("message", "Unknown error"))
        return True
    
    async def execute(
        self,
        model: str,
        method: str,
        record_ids: Optional[list] = None,
        args: Optional[list] = None,
        kwargs: Optional[dict] = None,
    ) -> Any:
        """Execute a method on model/records"""
        result = await self._request(
            "execute",
            model=model,
            method=method,
            record_ids=record_ids,
            args=args,
            kwargs_data=kwargs,
        )
        if result.get("error"):
            raise OdooError(result.get("message", "Unknown error"))
        return result.get("data", {}).get("result")
    
    async def close(self):
        """Close the HTTP client"""
        await self._client.aclose()


class OdooError(Exception):
    """Exception raised for Odoo-related errors"""
    pass


# Global client instance
_client: Optional[OdooClient] = None


def get_client() -> OdooClient:
    """Get or create the global Odoo client"""
    global _client
    if _client is None:
        _client = OdooClient()
    return _client


async def close_client():
    """Close the global client"""
    global _client
    if _client:
        await _client.close()
        _client = None
