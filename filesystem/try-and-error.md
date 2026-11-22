# Python MCP Server v2 — Learning Notes

## 1. Project Goal

Build and test a custom filesystem MCP server using Python and the MCP SDK v2.

The goal was to replace an existing Node.js filesystem MCP server with a Python implementation and learn how MCP servers expose Python functions as tools.

## 2. Original Node.js MCP Configuration

The starting configuration was:

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "C:\\Users\\username\\Desktop",
        "C:\\Users\\username\\Downloads"
      ]
    }
  }
}
```

### What it means

| Component | Purpose |
|---|---|
| `mcpServers` | Defines MCP servers available to a client |
| `filesystem` | Server name |
| `command` | Executable used to start the server |
| `npx` | Runs a Node.js package |
| `server-filesystem` | Existing filesystem MCP server |
| Folder paths | Directories the server can access |

Our goal was to create our own Python server rather than use the prebuilt Node.js server.

## 3. Project Structure

Project location:

```text
C:\_DATA\work\mcp\filesystem
└── filesystem_server.py
```

## 4. Install the Python MCP SDK

Run:

```cmd
py -m pip install "mcp[cli]"
```

The SDK provides libraries for creating MCP servers, registering tools, defining schemas, handling MCP communication, and supporting development workflows.

## 5. MCP SDK Version Mismatch

Initially, the code used the older v1 import:

```python
from mcp.server.fastmcp import FastMCP
```

But MCP SDK v2 was installed, resulting in:

```text
ModuleNotFoundError: No module named 'mcp.server.fastmcp'
```

We decided to use v2 instead of downgrading.

The v2 initialization we used:

```python
from mcp.server import MCPServer

mcp = MCPServer("Filesystem Server")
```

The decorator-based tool registration remained similar:

```python
@mcp.tool()
```

> SDK APIs can change between major versions. Check the installed version and corresponding documentation when troubleshooting.

## 6. Filesystem MCP Server Tools

Our server exposes these tools:

| Tool | Purpose |
|---|---|
| `list_directory` | List files and folders in a directory |
| `read_file` | Read a text file |
| `write_file` | Write or overwrite a text file |
| `create_directory` | Create a directory |
| `search_files` | Recursively search for files using a glob pattern |

## 7. Tool Registration with `@mcp.tool()`

Example:

```python
@mcp.tool()
def list_directory(path: str) -> list[str]:
    """List files and folders in a directory."""
```

The decorator registers a regular Python function as an MCP tool.

The SDK uses function information, type annotations, and documentation to expose tool metadata and an input schema to MCP clients.

Example tool information:

| Attribute | Example |
|---|---|
| Tool name | `list_directory` |
| Input | `path` |
| Input type | String |
| Description | List files and folders in a directory |

## 8. Path Access Restrictions

We restricted filesystem access to explicitly permitted folders.

Initially, the configured folders were:

```python
ALLOWED_DIRS = [
    Path(r"C:\Users\imamd\Desktop").resolve(),
    Path(r"C:\Users\imamd\Downloads").resolve(),
]
```

The server uses a validation function:

```python
def validate_path(path: str) -> Path:
    target = Path(path).resolve()

    for base in ALLOWED_DIRS:
        if target == base or base in target.parents:
            return target

    raise ValueError("Access denied: path is outside allowed directories")
```

### Why path validation?

The MCP server should not have unrestricted access to the computer. Path validation restricts tool operations to permitted locations.

- Allowed: paths inside configured folders.
- Blocked: paths outside configured folders.

## 9. OneDrive Desktop Path Troubleshooting

The first test failed because the actual Desktop was located under OneDrive:

```text
C:\Users\imamd\OneDrive\Desktop
```

Instead of the initially configured path:

```text
C:\Users\imamd\Desktop
```

We temporarily added debugging code to reveal the exception:

```python
except Exception as e:
    return [f"DEBUG ERROR: {type(e).__name__}: {e}"]
```

The resulting error was:

```text
DEBUG ERROR: ValueError: Access denied: path is outside allowed directories
```

This indicated that path validation was functioning, but the actual directory was not included in the allowed list.

We updated the configuration:

```python
ALLOWED_DIRS = [
    Path(r"C:\Users\imamd\OneDrive\Desktop").resolve(),
    Path(r"C:\Users\imamd\Downloads").resolve(),
]
```

After this change, the OneDrive Desktop path was authorized.

**Note:** Downloads remains configured as `C:\Users\imamd\Downloads`. If Downloads is redirected, update that path too.

## 10. Node.js Dependency for MCP Inspector

When running:

```cmd
mcp dev filesystem_server.py
```

we encountered:

```text
npx not found
```

The MCP development CLI uses `npx` to launch MCP Inspector tooling. `npx` is supplied by Node.js/npm.

Node.js was installed to support the Inspector launch workflow.

**Node.js does not run our filesystem functions. Those functions are written and executed in Python.**

## 11. Install `uv`

The Inspector launch configuration used `uv` to run the server, and we encountered:

```text
'uv' is not recognized as an internal or external command
```

`uv` is a Python package/environment manager and executable. We installed it to support the generated development launch command.

## 12. Launch MCP Inspector

From the project directory:

```cmd
cd C:\_DATA\work\mcp\filesystem
mcp dev filesystem_server.py
```

MCP Inspector is a development and debugging interface. It lets us:

- Connect to an MCP server.
- Discover available tools.
- Inspect tool names, descriptions and schemas.
- Manually execute tools.
- View responses and diagnose errors.

## 13. Testing the Tools

### Test `list_directory`

Input:

```json
{
  "path": "C:\\Users\\imamd\\OneDrive\\Desktop"
}
```

The first test against `C:\Users\imamd\Desktop` failed because the Desktop was redirected to OneDrive and wasn't authorized.

After adding the correct OneDrive path to `ALLOWED_DIRS`, the test succeeded.

### Other suggested tests

| Tool | Input example |
|---|---|
| `list_directory` | `C:\Users\imamd\OneDrive\Desktop` |
| `search_files` | Path: `C:\Users\imamd\Downloads`, Pattern: `*.pdf` |
| `create_directory` | `C:\Users\imamd\OneDrive\Desktop\MCP_Test` |
| `write_file` | `C:\Users\imamd\OneDrive\Desktop\MCP_Test\hello.txt` |
| `read_file` | `C:\Users\imamd\OneDrive\Desktop\MCP_Test\hello.txt` |

For `write_file`, provide the file path and content as separate arguments.

## 14. End-to-End MCP Tool Flow

1. The MCP client requests available tools.
2. The server exposes tool names, descriptions, and input schemas.
3. The client selects a tool.
4. The client sends the tool name and arguments.
5. Python executes the registered function.
6. The function returns a result.
7. The client displays the result.

```text
MCP Client / Inspector
        |
        | MCP request (stdio)
        v
Python MCP Server (MCP SDK v2)
        |
        | Tool execution
        v
Python filesystem function
        |
        v
Authorized Windows folders
        |
        v
Result returned to client
```

## 15. Concepts Learned

| Concept | What was learned |
|---|---|
| MCP SDK | Installed and used the Python SDK |
| SDK version | Recognized and resolved v1/v2 API mismatch |
| MCP server | Created a server with the v2 API |
| MCP tools | Registered Python functions using `@mcp.tool()` |
| Tool schemas | Exposed arguments and types to an MCP client |
| Path validation | Restricted access to authorized directories |
| Debugging | Used exception details to diagnose errors |
| Node.js | Installed as a prerequisite for Inspector tooling |
| `uv` | Installed for the Inspector launch workflow |
| MCP Inspector | Connected and tested tools interactively |
| Tool execution | Successfully called a tool and received results |

## 16. Architecture

```text
MCP Client / Inspector
        |
        | MCP protocol (stdio)
        v
Python MCP Server
filesystem_server.py
        |
        +-- list_directory
        +-- read_file
        +-- write_file
        +-- create_directory
        +-- search_files
        |
        v
Path validation
        |
        v
Authorized Windows directories
(OneDrive Desktop and Downloads)
```

## 17. Suggested Learning Roadmap

| Stage | Project | Skills |
|---|---|---|
| Completed | Filesystem MCP | Server, tools, validation, testing |
| 2 | Calculator MCP | Tool inputs, outputs, types |
| 3 | REST API MCP | HTTP, API calls, JSON, authentication |
| 4 | Monitoring MCP | Health checks, response time, error handling |
| 5 | Database MCP | SQL, query security, structured data |
| 6 | Salesforce MCP | CRM integration |
| 7 | MuleSoft MCP bridge | Enterprise integration and orchestration |

### Recommended next project

Build a REST API monitoring MCP server. It will introduce API calls, HTTP response handling, structured results, error handling, and monitoring concepts that are useful for enterprise integration and MuleSoft work.

---

## 18. Useful Commands

```cmd
:: Check Python
py --version

:: Check MCP package
py -m pip show mcp

:: Run the Python script directly
py filesystem_server.py

:: Launch MCP Inspector development mode
mcp dev filesystem_server.py

:: Change to project directory
cd C:\_DATA\work\mcp\filesystem
```

## 19. Important Security Reminder

This is a learning implementation, not a hardened production filesystem server.

- Restrict access to only necessary folders.
- Avoid exposing sensitive files.
- Be careful with overwriting or creating files.
- Validate paths and consider symlink/path edge cases.
- Use appropriate authorization and auditing before deploying MCP servers in an enterprise environment.
