"""
AD MCP Bridge Server - Main MCP Server Implementation

This server exposes Odoo data through the Model Context Protocol (MCP),
allowing AI assistants to interact with Odoo using natural language.
"""
import json
from typing import Optional
from mcp.server.fastmcp import FastMCP
from .odoo_client import get_client, OdooError
from .config import settings


# Initialize MCP server
mcp = FastMCP(
    name="AD MCP Bridge Server",
    instructions="Connect AI assistants to Odoo data through MCP. Use the available tools to search, read, create, update, and delete records in Odoo."
)


# ============================================================================
# RESOURCES - Data endpoints for read access
# ============================================================================

@mcp.resource("odoo://models")
async def resource_models() -> str:
    """List all models enabled for MCP access"""
    client = get_client()
    models = await client.list_models()
    return json.dumps(models, indent=2, default=str)


@mcp.resource("odoo://model/{model_name}/fields")
async def resource_model_fields(model_name: str) -> str:
    """Get field definitions for a specific model"""
    client = get_client()
    fields = await client.get_fields(model_name)
    return json.dumps(fields, indent=2, default=str)


@mcp.resource("odoo://{model_name}/record/{record_id}")
async def resource_record(model_name: str, record_id: str) -> str:
    """Get a specific record by ID - Example: odoo://res.partner/record/1"""
    client = get_client()
    record = await client.read(model_name, int(record_id), None)
    return format_record(model_name, record)


@mcp.resource("odoo://{model_name}/count")
async def resource_count(model_name: str) -> str:
    """Get count of all records in a model"""
    client = get_client()
    count = await client.count(model_name, [])
    return json.dumps({"model": model_name, "count": count})


# ============================================================================
# TOOLS - Search and Read Operations
# ============================================================================

@mcp.tool()
async def search_records(
    model: str,
    domain: Optional[list] = None,
    fields: Optional[list] = None,
    limit: int = 80,
    offset: int = 0,
    order: Optional[str] = None,
) -> str:
    """
    Search for records in an Odoo model.
    
    Args:
        model: The Odoo model name (e.g., 'res.partner', 'sale.order')
        domain: Search filter as Odoo domain list (e.g., [['is_company', '=', True]])
                Common operators: =, !=, >, <, >=, <=, like, ilike, in, not in
        fields: List of fields to return (empty = smart defaults)
        limit: Maximum records to return (default 80)
        offset: Number of records to skip (for pagination)
        order: Sort order (e.g., 'name asc, id desc')
    
    Returns:
        JSON list of matching records
    
    Examples:
        - Find all companies: model='res.partner', domain=[['is_company', '=', True]]
        - Find orders from this month: model='sale.order', domain=[['date_order', '>=', '2024-01-01']]
        - Find unpaid invoices: model='account.move', domain=[['payment_state', '!=', 'paid']]
    """
    try:
        client = get_client()
        records = await client.search(
            model=model,
            domain=domain,
            fields=fields,
            limit=min(limit, settings.max_records),
            offset=offset,
            order=order,
        )
        
        if not records:
            return f"No records found in {model} matching the criteria."
        
        return format_records(model, records)
        
    except OdooError as e:
        return f"Error searching {model}: {str(e)}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"


@mcp.tool()
async def get_record(
    model: str,
    record_id: int,
    fields: Optional[list] = None,
) -> str:
    """
    Get a specific record by ID.
    
    Args:
        model: The Odoo model name
        record_id: The ID of the record to retrieve
        fields: List of fields to return (empty = all accessible fields)
    
    Returns:
        JSON object with the record data
    
    Example:
        Get customer details: model='res.partner', record_id=5
    """
    try:
        client = get_client()
        record = await client.read(model, record_id, fields)
        
        if not record:
            return f"Record {record_id} not found in {model}."
        
        return format_record(model, record)
        
    except OdooError as e:
        return f"Error reading {model} record {record_id}: {str(e)}"


@mcp.tool()
async def count_records(
    model: str,
    domain: Optional[list] = None,
) -> str:
    """
    Count records matching a domain.
    
    Args:
        model: The Odoo model name
        domain: Search filter as Odoo domain list
    
    Returns:
        Number of matching records
    
    Example:
        Count unpaid invoices: model='account.move', domain=[['payment_state', '!=', 'paid']]
    """
    try:
        client = get_client()
        count = await client.count(model, domain)
        
        domain_str = f" matching {domain}" if domain else ""
        return f"Found {count} records in {model}{domain_str}."
        
    except OdooError as e:
        return f"Error counting {model}: {str(e)}"


# ============================================================================
# TOOLS - Model Information
# ============================================================================

@mcp.tool()
async def list_models() -> str:
    """
    List all Odoo models available for MCP access.
    
    Returns:
        List of models with their permissions (read, create, update, delete)
    """
    try:
        client = get_client()
        models = await client.list_models()
        
        if not models:
            return "No models are currently enabled for MCP access."
        
        lines = ["# Available Models\n"]
        for m in models:
            perms = []
            if m.get('can_read'): perms.append('read')
            if m.get('can_create'): perms.append('create')
            if m.get('can_write'): perms.append('update')
            if m.get('can_delete'): perms.append('delete')
            
            perm_str = ", ".join(perms) if perms else "no permissions"
            lines.append(f"- **{m['model']}** ({m.get('name', 'Unknown')}): {perm_str}")
        
        return "\n".join(lines)
        
    except OdooError as e:
        return f"Error listing models: {str(e)}"


@mcp.tool()
async def get_model_fields(
    model: str,
    field_types: Optional[list] = None,
) -> str:
    """
    Get field definitions for an Odoo model.
    
    Args:
        model: The Odoo model name
        field_types: Optional list of types to filter (e.g., ['many2one', 'char'])
    
    Returns:
        List of fields with their types and descriptions
    """
    try:
        client = get_client()
        fields = await client.get_fields(model)
        
        if field_types:
            fields = [f for f in fields if f.get('type') in field_types]
        
        if not fields:
            return f"No fields found for {model}."
        
        # Group by type for better readability
        by_type = {}
        for f in fields:
            ftype = f.get('type', 'unknown')
            if ftype not in by_type:
                by_type[ftype] = []
            by_type[ftype].append(f)
        
        lines = [f"# Fields for {model}\n"]
        for ftype, flist in sorted(by_type.items()):
            lines.append(f"\n## {ftype.title()} Fields")
            for f in sorted(flist, key=lambda x: x['name']):
                req = " (required)" if f.get('required') else ""
                ro = " [readonly]" if f.get('readonly') else ""
                lines.append(f"- **{f['name']}**: {f.get('label', '')}{req}{ro}")
        
        return "\n".join(lines)
        
    except OdooError as e:
        return f"Error getting fields for {model}: {str(e)}"


# ============================================================================
# TOOLS - Create, Update, Delete Operations
# ============================================================================

@mcp.tool()
async def create_record(
    model: str,
    values: dict,
) -> str:
    """
    Create a new record in Odoo.
    
    Args:
        model: The Odoo model name
        values: Dictionary of field values for the new record
    
    Returns:
        Success message with the new record ID
    
    Example:
        Create customer: model='res.partner', values={'name': 'New Customer', 'email': 'new@example.com'}
    """
    try:
        client = get_client()
        record_id = await client.create(model, values)
        
        return f"✅ Successfully created {model} record with ID {record_id}."
        
    except OdooError as e:
        return f"❌ Error creating {model}: {str(e)}"


@mcp.tool()
async def update_record(
    model: str,
    record_id: int,
    values: dict,
) -> str:
    """
    Update an existing record in Odoo.
    
    Args:
        model: The Odoo model name
        record_id: The ID of the record to update
        values: Dictionary of field values to update
    
    Returns:
        Success message
    
    Example:
        Update customer phone: model='res.partner', record_id=5, values={'phone': '123-456-7890'}
    """
    try:
        client = get_client()
        await client.write(model, record_id, values)
        
        fields_updated = ", ".join(values.keys())
        return f"✅ Successfully updated {model} record {record_id}. Fields: {fields_updated}"
        
    except OdooError as e:
        return f"❌ Error updating {model} record {record_id}: {str(e)}"


@mcp.tool()
async def delete_record(
    model: str,
    record_id: int,
) -> str:
    """
    Delete a record from Odoo.
    
    Args:
        model: The Odoo model name
        record_id: The ID of the record to delete
    
    Returns:
        Success message
    
    ⚠️ WARNING: This action is irreversible!
    """
    try:
        client = get_client()
        await client.unlink(model, record_id)
        
        return f"✅ Successfully deleted {model} record {record_id}."
        
    except OdooError as e:
        return f"❌ Error deleting {model} record {record_id}: {str(e)}"


# ============================================================================
# TOOLS - Advanced Operations
# ============================================================================

@mcp.tool()
async def execute_method(
    model: str,
    method: str,
    record_ids: Optional[list] = None,
    args: Optional[list] = None,
    kwargs: Optional[dict] = None,
) -> str:
    """
    Execute a custom method on an Odoo model.
    
    Args:
        model: The Odoo model name
        method: The method name to call
        record_ids: Optional list of record IDs to call the method on
        args: Positional arguments for the method
        kwargs: Keyword arguments for the method
    
    Returns:
        Method result
    
    ⚠️ Note: This requires special permission in Odoo settings.
    
    Example:
        Confirm sale order: model='sale.order', method='action_confirm', record_ids=[5]
    """
    try:
        client = get_client()
        result = await client.execute(model, method, record_ids, args, kwargs)
        
        if result is None:
            return f"✅ Method {method} executed successfully on {model}."
        
        return f"✅ Method {method} result: {json.dumps(result, indent=2, default=str)}"
        
    except OdooError as e:
        return f"❌ Error executing {method} on {model}: {str(e)}"


@mcp.tool()
async def get_record_name(
    model: str,
    record_id: int,
) -> str:
    """
    Get the display name of a record (useful for looking up references).
    
    Args:
        model: The Odoo model name
        record_id: The record ID
    
    Returns:
        Display name of the record
    """
    try:
        client = get_client()
        record = await client.read(model, record_id, ['display_name'])
        return record.get('display_name', f'{model},{record_id}')
    except OdooError as e:
        return f"Record not found: {str(e)}"


@mcp.tool()
async def search_and_read_one(
    model: str,
    domain: list,
    fields: Optional[list] = None,
) -> str:
    """
    Search and return the first matching record (convenience method).
    
    Args:
        model: The Odoo model name
        domain: Search filter as Odoo domain list
        fields: List of fields to return
    
    Returns:
        The first matching record or a message if not found
    """
    try:
        client = get_client()
        records = await client.search(model, domain, fields, limit=1)
        
        if not records:
            return f"No record found in {model} matching {domain}."
        
        return format_record(model, records[0])
        
    except OdooError as e:
        return f"Error: {str(e)}"


# ============================================================================
# HELPER FUNCTIONS - Output Formatting
# ============================================================================

def format_records(model: str, records: list) -> str:
    """Format a list of records for output"""
    if not records:
        return f"No records found in {model}."
    
    lines = [f"# Found {len(records)} records in {model}\n"]
    
    for rec in records:
        rec_id = rec.get('id', '?')
        name = rec.get('display_name') or rec.get('name') or f"ID {rec_id}"
        lines.append(f"## {name} (ID: {rec_id})")
        
        for key, value in rec.items():
            if key in ('id', 'display_name', 'name', '__last_update'):
                continue
            if value is None or value == '' or value is False:
                continue
            
            # Format different types
            if isinstance(value, list) and len(value) == 2 and isinstance(value[0], int):
                # Many2one field: [id, name]
                value = f"{value[1]} (ID: {value[0]})"
            elif isinstance(value, list):
                value = ", ".join(str(v) for v in value)
            
            lines.append(f"- **{key}**: {value}")
        
        lines.append("")  # Empty line between records
    
    return "\n".join(lines)


def format_record(model: str, record: dict) -> str:
    """Format a single record for output"""
    rec_id = record.get('id', '?')
    name = record.get('display_name') or record.get('name') or f"ID {rec_id}"
    
    lines = [f"# {model}: {name} (ID: {rec_id})\n"]
    
    # Group fields by type for readability
    basic_fields = []
    relation_fields = []
    other_fields = []
    
    for key, value in record.items():
        if key in ('id', 'display_name', '__last_update'):
            continue
        if value is None or value == '' or value is False:
            continue
        
        if isinstance(value, list) and len(value) == 2 and isinstance(value[0], int):
            # Many2one field
            relation_fields.append((key, f"{value[1]} (ID: {value[0]})"))
        elif isinstance(value, list):
            # O2M/M2M field
            if value:
                other_fields.append((key, f"{len(value)} items: {value[:5]}{'...' if len(value) > 5 else ''}"))
        elif isinstance(value, (str, int, float, bool)):
            basic_fields.append((key, value))
        else:
            other_fields.append((key, str(value)))
    
    if basic_fields:
        lines.append("## Basic Information")
        for key, value in basic_fields:
            lines.append(f"- **{key}**: {value}")
    
    if relation_fields:
        lines.append("\n## Related Records")
        for key, value in relation_fields:
            lines.append(f"- **{key}**: {value}")
    
    if other_fields:
        lines.append("\n## Other Data")
        for key, value in other_fields:
            lines.append(f"- **{key}**: {value}")
    
    return "\n".join(lines)


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main():
    """Entry point for the MCP server"""
    import argparse
    
    parser = argparse.ArgumentParser(description="AD MCP Bridge Server for Odoo")
    parser.add_argument(
        '--transport',
        default=settings.mcp_transport,
        choices=['stdio', 'streamable-http'],
        help='Transport protocol (default: stdio)'
    )
    parser.add_argument('--host', default=settings.mcp_host, help='Host for HTTP transport')
    parser.add_argument('--port', type=int, default=settings.mcp_port, help='Port for HTTP transport')
    
    args = parser.parse_args()
    
    # Configure transport
    if args.transport == 'streamable-http':
        mcp.run(transport='streamable-http', host=args.host, port=args.port)
    else:
        mcp.run(transport='stdio')


if __name__ == "__main__":
    main()
