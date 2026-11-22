
from pathlib import Path
from mcp.server import MCPServer

mcp = MCPServer("Filesystem Server")

# Directories this MCP server is allowed to access
ALLOWED_DIRS = [
    Path(r"C:\Users\imamd\OneDrive\Desktop").resolve(),
    Path(r"C:\Users\imamd\Downloads").resolve(),
]


def validate_path(path: str) -> Path:
    """Ensure a path is inside one of the permitted directories."""
    target = Path(path).resolve()

    for base in ALLOWED_DIRS:
        if target == base or base in target.parents:
            return target

    raise ValueError("Access denied: path is outside allowed directories")


# @mcp.tool()
# def list_directory(path: str) -> list[str]:
    # """List files and folders in a directory."""
    # target = validate_path(path)

    # if not target.is_dir():
        # raise ValueError("Directory does not exist")

    # return [item.name for item in target.iterdir()]

@mcp.tool()
def list_directory(path: str) -> list[str]:
    """List files and folders in a directory."""
    try:
        target = validate_path(path)

        if not target.is_dir():
            raise ValueError(f"Directory does not exist: {target}")

        return [item.name for item in target.iterdir()]

    except Exception as e:
        return [f"DEBUG ERROR: {type(e).__name__}: {e}"]


@mcp.tool()
def read_file(path: str) -> str:
    """Read the contents of a text file."""
    target = validate_path(path)

    if not target.is_file():
        raise ValueError("File does not exist")

    return target.read_text(encoding="utf-8")


@mcp.tool()
def write_file(path: str, content: str) -> str:
    """Write content to a text file."""
    target = validate_path(path)

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")

    return f"File written successfully: {target}"


@mcp.tool()
def create_directory(path: str) -> str:
    """Create a directory."""
    target = validate_path(path)

    target.mkdir(parents=True, exist_ok=True)

    return f"Directory created: {target}"


@mcp.tool()
def search_files(path: str, pattern: str) -> list[str]:
    """Search files recursively using a glob pattern."""
    target = validate_path(path)

    if not target.is_dir():
        raise ValueError("Directory does not exist")

    results = []

    for item in target.rglob(pattern):
        resolved_item = validate_path(str(item))
        results.append(str(resolved_item))

    return results


if __name__ == "__main__":
    mcp.run()
