#!/bin/bash
# holoviz-viz-mcp setup script
# Usage: bash setup.sh [client]
# Clients: claude-desktop, claude-code, cursor, vscode, all

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m'

echo ""
echo -e "${BOLD}holoviz-viz-mcp setup${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 1. Install the package
echo -e "${BLUE}[1/3]${NC} Installing holoviz-viz-mcp..."
pip install -e ".[test]" --quiet
echo -e "${GREEN}  Installed.${NC}"

# 2. Verify it works
echo -e "${BLUE}[2/3]${NC} Verifying installation..."
python -c "from holoviz_viz_mcp.server import mcp; print('  Server module loaded OK')"
echo -e "${GREEN}  Verified.${NC}"

# 3. Configure MCP client
CLIENT="${1:-}"
PYTHON_PATH=$(which python)
SERVER_CMD="holoviz-viz-mcp"

configure_claude_desktop() {
    CONFIG_DIR="$HOME/Library/Application Support/Claude"
    CONFIG_FILE="$CONFIG_DIR/claude_desktop_config.json"

    mkdir -p "$CONFIG_DIR"

    if [ -f "$CONFIG_FILE" ]; then
        # Check if already configured
        if python -c "import json; c=json.load(open('$CONFIG_FILE')); exit(0 if 'holoviz-viz' in c.get('mcpServers',{}) else 1)" 2>/dev/null; then
            echo -e "${GREEN}  Claude Desktop already configured.${NC}"
            return
        fi
        # Add to existing config
        python -c "
import json
with open('$CONFIG_FILE') as f:
    config = json.load(f)
config.setdefault('mcpServers', {})['holoviz-viz'] = {
    'command': '$SERVER_CMD'
}
with open('$CONFIG_FILE', 'w') as f:
    json.dump(config, f, indent=2)
"
    else
        # Create new config
        python -c "
import json
config = {'mcpServers': {'holoviz-viz': {'command': '$SERVER_CMD'}}}
with open('$CONFIG_FILE', 'w') as f:
    json.dump(config, f, indent=2)
"
    fi
    echo -e "${GREEN}  Claude Desktop configured. Restart Claude Desktop to activate.${NC}"
}

configure_claude_code() {
    claude mcp add holoviz-viz -- "$SERVER_CMD" 2>/dev/null || {
        echo "  Run manually: claude mcp add holoviz-viz -- $SERVER_CMD"
    }
    echo -e "${GREEN}  Claude Code configured.${NC}"
}

configure_cursor() {
    CONFIG_DIR="$HOME/.cursor"
    CONFIG_FILE="$CONFIG_DIR/mcp.json"

    mkdir -p "$CONFIG_DIR"

    if [ -f "$CONFIG_FILE" ]; then
        python -c "
import json
with open('$CONFIG_FILE') as f:
    config = json.load(f)
config.setdefault('mcpServers', {})['holoviz-viz'] = {
    'command': '$SERVER_CMD'
}
with open('$CONFIG_FILE', 'w') as f:
    json.dump(config, f, indent=2)
"
    else
        python -c "
import json
config = {'mcpServers': {'holoviz-viz': {'command': '$SERVER_CMD'}}}
with open('$CONFIG_FILE', 'w') as f:
    json.dump(config, f, indent=2)
"
    fi
    echo -e "${GREEN}  Cursor configured. Restart Cursor to activate.${NC}"
}

configure_vscode() {
    VSCODE_DIR=".vscode"
    mkdir -p "$VSCODE_DIR"
    SETTINGS_FILE="$VSCODE_DIR/settings.json"

    if [ -f "$SETTINGS_FILE" ]; then
        python -c "
import json
with open('$SETTINGS_FILE') as f:
    config = json.load(f)
config.setdefault('github.copilot.chat.mcpServers', {})['holoviz-viz'] = {
    'command': '$SERVER_CMD'
}
with open('$SETTINGS_FILE', 'w') as f:
    json.dump(config, f, indent=2)
"
    else
        python -c "
import json
config = {'github.copilot.chat.mcpServers': {'holoviz-viz': {'command': '$SERVER_CMD'}}}
with open('$SETTINGS_FILE', 'w') as f:
    json.dump(config, f, indent=2)
"
    fi
    echo -e "${GREEN}  VS Code Copilot configured.${NC}"
}

echo -e "${BLUE}[3/3]${NC} Configuring MCP client..."

case "$CLIENT" in
    claude-desktop)
        configure_claude_desktop
        ;;
    claude-code)
        configure_claude_code
        ;;
    cursor)
        configure_cursor
        ;;
    vscode)
        configure_vscode
        ;;
    all)
        echo "  Configuring all clients..."
        configure_claude_desktop
        configure_cursor
        configure_vscode
        echo "  For Claude Code, run: claude mcp add holoviz-viz -- $SERVER_CMD"
        ;;
    "")
        echo "  No client specified. Configure manually or re-run with:"
        echo ""
        echo "    bash setup.sh claude-desktop"
        echo "    bash setup.sh claude-code"
        echo "    bash setup.sh cursor"
        echo "    bash setup.sh vscode"
        echo "    bash setup.sh all"
        ;;
    *)
        echo "  Unknown client: $CLIENT"
        echo "  Supported: claude-desktop, claude-code, cursor, vscode, all"
        ;;
esac

echo ""
echo -e "${BOLD}Setup complete!${NC}"
echo ""
echo "Try these prompts in your AI assistant:"
echo "  1. \"Load the iris dataset and create a scatter plot of sepal length vs width colored by species\""
echo "  2. \"Create a crossfilter dashboard with scatter, histogram, and box plot\""
echo "  3. \"Create a streaming line chart\""
echo ""
echo "Run the local demo:  python demos/quick_demo.py"
echo "Run tests:           pytest tests/ -v"
echo ""
