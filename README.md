# TradingView MCP Server 📈

A **lightweight** Model Context Protocol (MCP) server for fetching TradingView chart snapshots. Uses Playwright for efficient browser automation with persistent sessions and cookie-based authentication.

> **Note**: This uses Playwright because TradingView renders charts client-side with JavaScript/Canvas. There is no pure HTTP API for chart images. This is the lightest possible working solution (~150MB RAM vs ~500MB with Selenium).

## ✨ Features

- 🪶 **Lightweight**: Playwright in headless mode (~150MB vs ~500MB with Selenium)
- 🚀 **Fast**: Persistent browser reuse, 3-5 seconds per chart
- 🔐 **Secure**: Session-based authentication via cookies
- 🎨 **Customizable**: Configure chart dimensions, intervals, and themes
- 🔧 **MCP Compatible**: Works with any MCP-enabled client (Claude Desktop, etc.)
- ♻️ **Efficient**: Reuses browser instances across multiple requests

## 📋 Prerequisites

- Python 3.10 or higher
- A TradingView account (free or paid)
- TradingView session cookies

## Table of Contents

- [Installation](#-installation)
- [Quick Start](#-quick-start)
- [Usage](#-usage)
- [Configuration](#-configuration)
- [Available Tools](#️-available-tools)
- [Symbol Format](#-symbol-format)
- [Troubleshooting](#-troubleshooting)
- [Performance](#-performance)
- [Contributing](#-contributing)

## 🚀 Installation

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/tradingview-mcp.git
cd tradingview-mcp
```

### 2. Create a virtual environment

```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt

# Install Playwright browsers (one-time setup, ~150MB download)
python -m playwright install chromium
```

### 4. Configure credentials

1. Copy `.env.example` to `.env`:
   ```bash
   # Windows
   copy .env.example .env
   
   # Linux/Mac
   cp .env.example .env
   ```

2. **Get your TradingView session cookies:**
   - Log into [TradingView](https://www.tradingview.com) in your browser
   - Press **F12** to open Developer Tools
   - Go to **Application** tab (Chrome) or **Storage** tab (Firefox)
   - Navigate to **Cookies** > `https://www.tradingview.com`
   - Find and copy these two cookie values:
     - `sessionid` → Copy the entire value
     - `sessionid_sign` → Copy the entire value
   
   > ⚠️ **Important**: Copy the full values including any special characters (slashes, equals signs, etc.). Don't add quotes or extra spaces.

3. Edit `.env` and paste your values:
   ```env
   TRADINGVIEW_SESSION_ID=your_actual_session_id_here
   TRADINGVIEW_SESSION_ID_SIGN=your_actual_session_id_sign_here
   ```
   
   Example (with fake values):
   ```env
   TRADINGVIEW_SESSION_ID=47zlhkbl2weohrhmjgufeg1o24droaod
   TRADINGVIEW_SESSION_ID_SIGN=v3:6S2OD9ta349/yqN0RdCeK3UKxTl/tJr4AOoPRUa0Crk=
   ```

### 5. Test your setup (Optional but recommended)

Create a test file `test.py`:

```python
import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from dotenv import load_dotenv
load_dotenv()

from tradingview_mcp.server import get_chart_snapshot

async def test():
    image = await get_chart_snapshot("BINANCE:BTCUSDT", "D", 1200, 600, "dark")
    if image:
        Path("test_chart.png").write_bytes(image)
        print(f"✅ Success! Chart saved to test_chart.png ({len(image)} bytes)")
    else:
        print("❌ Failed to fetch chart")

asyncio.run(test())
```

Run it:
```bash
python test.py
```

If successful, you'll see `test_chart.png` with a Bitcoin chart!

## 🎯 Usage

### Quick Start - Testing Locally

After installation, test the server:

```bash
python src/tradingview_mcp/server.py
```

The server will start and wait for MCP client connections via stdio.

### Configuration for Claude Desktop

Add this to your Claude Desktop config file:

**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`  
**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`  
**Linux**: `~/.config/Claude/claude_desktop_config.json`

**Option 1: Using .env file (Recommended)**
```json
{
  "mcpServers": {
    "tradingview": {
      "command": "python",
      "args": ["C:\\path\\to\\tradingview-mcp\\src\\tradingview_mcp\\server.py"],
      "cwd": "C:\\path\\to\\tradingview-mcp"
    }
  }
}
```

**Option 2: Inline credentials**
```json
{
  "mcpServers": {
    "tradingview": {
      "command": "python",
      "args": ["C:\\path\\to\\tradingview-mcp\\src\\tradingview_mcp\\server.py"],
      "env": {
        "TRADINGVIEW_SESSION_ID": "your_session_id",
        "TRADINGVIEW_SESSION_ID_SIGN": "your_session_id_sign"
      }
    }
  }
}
```

> 💡 **Tip**: Use absolute paths. On Windows, use double backslashes `\\` or forward slashes `/`.

**Restart Claude Desktop** and you'll see the TradingView tools available!

### Example Queries in Claude

Once configured, you can ask Claude:

```
- "Get me a daily chart of Bitcoin"
- "Show me AAPL on 1-hour timeframe"
- "Fetch a weekly chart for NASDAQ:TSLA with light theme"
- "Get BINANCE:ETHUSDT 5-minute chart"
- "Validate my TradingView session"
- "What timeframes are available?"
```

## 🛠️ Available Tools

### 1. `get_chart_snapshot`

Fetch a TradingView chart snapshot.

**Parameters:**
- `symbol` (required): Trading pair in TradingView format
  - Examples: `"BINANCE:BTCUSDT"`, `"NASDAQ:AAPL"`, `"BITSTAMP:BTCUSD"`
- `interval` (optional): Chart timeframe (default: `"D"`)
  - Minutes: `"1"`, `"5"`, `"15"`, `"30"`, `"60"`, `"240"`
  - Days/Weeks/Months: `"D"`, `"W"`, `"M"`
- `width` (optional): Image width in pixels (default: `1200`)
- `height` (optional): Image height in pixels (default: `600`)
- `theme` (optional): `"dark"` or `"light"` (default: `"dark"`)

**Example:**
```
Get me a daily chart of Bitcoin on Binance
```

### 2. `validate_session`

Check if your TradingView session credentials are valid.

**Example:**
```
Validate my TradingView session
```

### 3. `list_timeframes`

List all available chart timeframes/intervals.

**Example:**
```
What timeframes are available?
```

## 📊 Symbol Format

TradingView uses the format: `EXCHANGE:SYMBOL`

### Common Examples

| Symbol | Description |
|--------|-------------|
| `BINANCE:BTCUSDT` | Bitcoin/USDT on Binance |
| `NASDAQ:AAPL` | Apple Inc. on NASDAQ |
| `NYSE:TSLA` | Tesla Inc. on NYSE |
| `BITSTAMP:BTCUSD` | Bitcoin/USD on Bitstamp |
| `FX:EURUSD` | EUR/USD forex pair |
| `COINBASE:ETHUSD` | Ethereum/USD on Coinbase |

### Finding Symbol Names

1. Go to [TradingView](https://www.tradingview.com)
2. Search for your desired asset
3. Look at the URL or chart title for the format `EXCHANGE:SYMBOL`

## 🔧 Architecture

This MCP server uses **Playwright for lightweight browser automation**:

1. **Authentication**: Session cookies passed to browser context
2. **Chart Generation**: Playwright navigates to TradingView and captures screenshots
3. **Efficiency**: Persistent browser instances reused across requests
4. **MCP Protocol**: Communicates via stdio with MCP clients

**Why Playwright (Not Pure HTTP)?**

- TradingView renders charts client-side with JavaScript/Canvas
- No server-side API exists for chart image generation
- Playwright is lighter than Selenium (~150MB vs ~500MB RAM)
- Headless mode with optimized flags minimizes resource usage
- Browser reuse makes subsequent requests very fast (1-2 seconds)

✅ **This is the lightest possible approach for TradingView charts**

## 🐛 Troubleshooting

### Cookie/Authentication Issues

**Problem**: "Session credentials are not working" or "Invalid session"

**Solutions**:
1. **Check for trailing commas or spaces**: Make sure your `.env` file has no extra characters
   ```env
   # ❌ Wrong (has comma)
   TRADINGVIEW_SESSION_ID=abc123,
   
   # ✅ Correct
   TRADINGVIEW_SESSION_ID=abc123
   ```

2. **Refresh cookies**: Session cookies expire after ~30 days
   - Log out and back into TradingView
   - Get fresh cookies from Developer Tools
   - Update your `.env` file

3. **Check you're logged in**: Make sure you're logged into TradingView when copying cookies

4. **Copy entire value**: Include special characters (=, /, :, etc.)

### Symbol Not Found

**Problem**: "Failed to fetch chart snapshot"

**Solutions**:
1. Use correct format: `EXCHANGE:SYMBOL` (all uppercase)
   - ✅ `BINANCE:BTCUSDT`
   - ❌ `btcusdt` or `binance:btcusdt`

2. Verify symbol exists on TradingView.com

3. Test with a known symbol first: `BINANCE:BTCUSDT` or `NASDAQ:AAPL`

### Timeout Errors

**Problem**: "Timeout exceeded" or slow performance

**Solutions**:
1. Check internet connection and TradingView.com accessibility
2. First request takes longer (5-8s) while browser starts
3. Subsequent requests are faster (3-5s) due to browser reuse
4. If persistent, restart the MCP server

### Playwright Installation Issues

**Problem**: "Playwright not found" or browser download fails

**Solutions**:
```bash
# Reinstall Playwright
pip uninstall playwright
pip install playwright

# Install browsers again
python -m playwright install chromium

# If still failing, install system dependencies (Linux)
sudo playwright install-deps
```

### Claude Desktop Not Recognizing Server

**Problem**: Tools don't appear in Claude Desktop

**Solutions**:
1. Check JSON syntax in config file (use a JSON validator)
2. Use **absolute paths** (not relative)
3. Verify Python path is correct:
   ```bash
   # Windows
   where python
   
   # Mac/Linux
   which python
   ```
4. **Completely restart** Claude Desktop (not just reload)
5. Check Claude logs for errors:
   - Windows: `%APPDATA%\Claude\logs\`
   - Mac: `~/Library/Logs/Claude/`

### Performance Issues

**Problem**: High memory usage or slow responses

**Tips**:
- Memory usage: ~150MB is normal for Playwright
- First chart: 5-8 seconds (browser startup)
- Subsequent charts: 3-5 seconds
- Browser is reused across requests for efficiency
- If memory grows over time, restart the server

## ⚡ Performance

| Metric | Value | Notes |
|--------|-------|-------|
| **Memory Usage** | ~150MB | Playwright headless browser |
| **First Request** | 5-8 seconds | Browser startup + chart load |
| **Subsequent Requests** | 3-5 seconds | Browser reuse (persistent) |
| **Image Size** | 50-200KB | PNG format, varies by dimensions |
| **Browser** | Chromium | ~150MB download (one-time) |

**Comparison with Alternatives:**

| Approach | Memory | Speed | Status |
|----------|--------|-------|--------|
| Pure HTTP | ~50MB | 1-2s | ❌ Impossible (no API exists) |
| Selenium | ~500MB | 10-15s | ⚠️ Works but heavy |
| **Playwright** | **~150MB** | **3-5s** | ✅ **Best option** |

## 🔒 Security Notes

- ⚠️ **Never commit your `.env` file** - it contains your session credentials
- ⚠️ **Don't share your session cookies** - they provide full account access
- ⚠️ **Rotate cookies regularly** - they expire after ~30 days
- ✅ `.env` is in `.gitignore` by default
- ✅ Use environment variables or secure credential management in production

## 📝 Development

### Project Structure

```
tradingview-mcp/
├── src/
│   └── tradingview_mcp/
│       ├── __init__.py
│       └── server.py          # Main MCP server
├── .env.example               # Template for credentials
├── .gitignore
├── README.md
├── requirements.txt           # Python dependencies
└── pyproject.toml            # Project metadata
```

### Running Tests

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest
```

### Code Formatting

```bash
# Format code
black src/

# Lint code
ruff check src/
```

## 🤝 Contributing

Contributions are welcome! Here's how:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Test thoroughly
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

**Development Setup:**
```bash
pip install -e ".[dev]"
black src/
ruff check src/
```

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [TradingView](https://www.tradingview.com) - Excellent charting platform
- [Anthropic](https://www.anthropic.com) - Model Context Protocol
- [Playwright](https://playwright.dev) - Browser automation

## ⚠️ Disclaimer

This is an **unofficial** tool and is not affiliated with, endorsed by, or connected to TradingView. Use at your own risk and in accordance with TradingView's Terms of Service. Respect rate limits and be mindful of your usage.

## � Support & Issues

- 🐛 **Bug Reports**: [GitHub Issues](https://github.com/yourusername/tradingview-mcp/issues)
- 💬 **Questions**: [GitHub Discussions](https://github.com/yourusername/tradingview-mcp/discussions)
- 📧 **Email**: your.email@example.com

## 📊 Project Stats

- **Version**: 0.1.0
- **Python**: 3.10+
- **Memory**: ~150MB
- **Response Time**: 3-5 seconds
- **License**: MIT

---

**Made with ❤️ by the trading community**

*Star ⭐ this repo if you find it useful!*
