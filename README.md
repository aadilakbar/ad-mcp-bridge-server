# MCP Odoo Bridge Server

[![MCP](https://img.shields.io/badge/MCP-Compatible-green)](https://modelcontextprotocol.io/)
[![Odoo](https://img.shields.io/badge/Odoo-17.0%20%7C%2018.0%20%7C%2019.0-purple)](https://www.odoo.com/)
[![Python](https://img.shields.io/badge/Python-3.10+-blue)](https://python.org/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue)](LICENSE)

> **Licensed under the Apache License, Version 2.0** - See [LICENSE](LICENSE) for details.

A [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server that enables AI assistants like **Claude** to interact with **Odoo** data using natural language.

## 🎯 What is MCP?

The [Model Context Protocol](https://modelcontextprotocol.io/introduction) is an open standard by Anthropic that enables AI assistants to securely connect to external data sources. This server acts as a bridge between Claude (or other MCP clients) and your Odoo instance.

**Learn more:** [MCP Documentation](https://modelcontextprotocol.io/docs)

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🔍 **Search Records** | Find records using natural language or Odoo domain syntax |
| 📖 **Read Records** | Get detailed record information by ID |
| 📊 **Count Records** | Get counts matching criteria |
| ➕ **Create Records** | Create new records (with permission) |
| ✏️ **Update Records** | Modify existing records (with permission) |
| 🗑️ **Delete Records** | Remove records (with permission) |
| 📋 **List Models** | Discover available models |
| 🔧 **Get Fields** | Understand model structure |
| ⚡ **Execute Methods** | Run custom methods (if enabled) |
| 🔐 **API Key Auth** | Secure authentication via API keys |
| 📝 **Audit Logging** | All operations logged for compliance |

---

## 📋 Prerequisites

1. **Odoo** instance (17.0, 18.0, or 19.0 recommended)
2. **Python 3.10+** installed
3. **AD Odoo MCP Bridge** module installed in Odoo (see [Odoo Module](#odoo-module))

---

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/ad-mcp-bridge-server.git
cd ad-mcp-bridge-server
```

### 2. Install Dependencies

```bash
pip install -e .
```

Or with uv:
```bash
uv pip install -e .
```

### 3. Install the Odoo Module

Install the `ad_odoo_mcp_bridge` module in your Odoo instance:
1. Add the module folder to your Odoo addons path
2. Go to **Apps** → Install **"AD Odoo MCP Bridge"**

---

## ⚙️ Configuration

### Environment Variables

The server requires the following environment variables:

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `ODOO_URL` | Yes | Your Odoo instance URL | `https://mycompany.odoo.com` |
| `ODOO_API_KEY` | Yes* | API key for authentication | `0ef5b399e9ee9c11b053dfb6eeba8de473c29fcd` |
| `ODOO_USER` | Yes* | Username (if not using API key) | `admin` |
| `ODOO_PASSWORD` | Yes* | Password (if not using API key) | `admin` |
| `ODOO_DB` | No | Database name (auto-detected if not set) | `mycompany` |
| `ODOO_MAX_RECORDS` | No | Default max records per query (default: `100`) | `200` |
| `ODOO_TIMEOUT` | No | Request timeout in seconds (default: `30`) | `60` |
| `ODOO_YOLO` | No | YOLO mode - bypasses MCP security (⚠️ DEV ONLY) | `off`, `read`, `true` |

> **\* Authentication**: You must provide either `ODOO_API_KEY` **or** both `ODOO_USER` and `ODOO_PASSWORD`.

#### MCP Transport Options

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `MCP_TRANSPORT` | No | Transport type: `stdio` or `streamable-http` (default: `stdio`) | `streamable-http` |
| `MCP_HOST` | No | Host for HTTP transport (default: `localhost`) | `0.0.0.0` |
| `MCP_PORT` | No | Port for HTTP transport (default: `8000`) | `8080` |

#### YOLO Mode Values

| Value | Description |
|-------|-------------|
| `off` | All operations require explicit MCP Bridge permissions (default) |
| `read` | Allows read-only operations on all models without configuration |
| `true` | **⚠️ DANGEROUS** - Allows all operations including write/delete without restrictions |

> **⚠️ Warning**: YOLO mode bypasses security checks and should **NEVER** be used in production. It's intended only for local development and testing.

### Create a `.env` File (Optional)

```env
ODOO_URL=https://mycompany.odoo.com
ODOO_DB=mycompany
ODOO_API_KEY=your-api-key-here
```

---

## 🔌 Usage with Claude Desktop

### Step 1: Generate API Key in Odoo

1. Go to **MCP Bridge → Configuration → API Keys**
2. Click **Create** → Select user → **Generate Key**
3. Copy the key (shown only once!)

### Step 2: Configure Claude Desktop

Edit `claude_desktop_config.json`:

**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`  
**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "odoo": {
      "command": "python",
      "args": ["-m", "ad_mcp_bridge_server"],
      "cwd": "/path/to/ad-mcp-bridge-server/src",
      "env": {
        "ODOO_URL": "http://localhost:8069",
        "ODOO_DB": "your_database",
        "ODOO_API_KEY": "your-api-key"
      }
    }
  }
}
```

> **Windows Note:** Use the full Python path if needed:
> ```json
> "command": "C:\\path\\to\\venv\\Scripts\\python.exe"
> ```

### Step 3: Restart Claude Desktop

Close and reopen Claude Desktop. You should see the 🔧 Tools icon.

### Step 4: Start Chatting!

Try these prompts:
- *"Show me all customers from the United States"*
- *"What's the status of order SO/2024/0153?"*
- *"Create a new lead for ABC Company"*
- *"How many unpaid invoices do we have?"*

---

## 🔌 Usage with VS Code

Create `.vscode/mcp.json` in your workspace:

```json
{
  "servers": {
    "odoo": {
      "command": "python",
      "args": ["-m", "ad_mcp_bridge_server"],
      "cwd": "/path/to/ad-mcp-bridge-server/src",
      "env": {
        "ODOO_URL": "http://localhost:8069",
        "ODOO_DB": "your_database",
        "ODOO_API_KEY": "your-api-key"
      }
    }
  }
}
```

---

## 🧪 Testing with MCP Inspector

Use the official MCP debugging tool:

```bash
npx @modelcontextprotocol/inspector python -m ad_mcp_bridge_server
```

This opens a web UI to test all tools interactively.

---

## 🏗️ Odoo Module

This MCP server requires the **AD Odoo MCP Bridge** module installed in Odoo.

### Compatibility

| Odoo Version | Status |
|--------------|--------|
| 19.0 | ✅ Fully Supported |
| 18.0 | ✅ Supported |
| 17.0 | ✅ Supported |
| 16.0 | ✅ Supported |

### Module Features

- **Model Configuration**: Choose which models AI can access
- **Permission Control**: Set read/create/update/delete per model
- **API Key Management**: Generate and manage API keys
- **Audit Logging**: Track all AI operations
- **Rate Limiting**: Control request frequency
- **YOLO Mode**: Quick access mode for development

### Module Installation

1. Copy `ad_odoo_mcp_bridge` folder to your Odoo addons path
2. Restart Odoo
3. Go to **Apps** → Remove "Apps" filter → Search "MCP" → Install

---

## 🔐 Security

- **API Key Authentication**: All requests require a valid API key
- **Permission Inheritance**: AI inherits Odoo user's permissions
- **Audit Trail**: All operations logged with IP, timestamp, and details
- **Rate Limiting**: Configurable per-key request limits
- **Field Exclusions**: Sensitive fields can be blocked

---

## 📚 API Endpoints (Odoo Module)

The Odoo module exposes these JSON-RPC endpoints:

| Endpoint | Description |
|----------|-------------|
| `GET /mcp/health` | Health check |
| `POST /mcp/info` | Server information |
| `POST /mcp/models` | List enabled models |
| `POST /mcp/fields` | Get model fields |
| `POST /mcp/search` | Search records |
| `POST /mcp/read` | Read record by ID |
| `POST /mcp/count` | Count records |
| `POST /mcp/create` | Create record |
| `POST /mcp/write` | Update record |
| `POST /mcp/unlink` | Delete record |
| `POST /mcp/execute` | Execute method |

---

## 🛠️ Development

### Run Locally

```bash
cd src
export ODOO_URL=http://localhost:8069
export ODOO_DB=mydb
export ODOO_API_KEY=your-key
python -m ad_mcp_bridge_server
```

### Project Structure

```
ad-mcp-bridge-server/
├── src/
│   └── ad_mcp_bridge_server/
│       ├── __init__.py
│       ├── __main__.py      # Entry point
│       ├── config.py        # Pydantic settings
│       ├── odoo_client.py   # Odoo HTTP client
│       └── server.py        # MCP server & tools
├── pyproject.toml
├── README.md
└── .env.example
```

---

## 📖 MCP Resources

- [Model Context Protocol Specification](https://modelcontextprotocol.io/specification)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [Claude Desktop MCP Setup](https://modelcontextprotocol.io/quickstart/user)
- [Building MCP Servers](https://modelcontextprotocol.io/quickstart/server)

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## ☕ Support

Thank you for using this project! If you find it helpful and would like to support my work, kindly consider buying me a coffee. Your support is greatly appreciated!

<a href="https://ko-fi.com/aadilakbar" target="_blank">
  <img src="https://ko-fi.com/img/githubbutton_sm.svg" alt="Buy Me a Coffee at ko-fi.com" />
</a>

And don't forget to give the project a ⭐ star if you like it!

---

## 📄 License

This project is licensed under the **Apache License 2.0** - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- [Anthropic](https://anthropic.com/) for Claude and MCP
- [Odoo](https://odoo.com/) for the amazing ERP platform
- [FastMCP](https://github.com/jlowin/fastmcp) for the Python MCP framework

---

## 📝 About

A Model Context Protocol (MCP) server that enables AI assistants to securely interact with Odoo ERP systems through standardized resources and tools for data retrieval and manipulation.

**Made with ❤️ for the Odoo and AI community**
