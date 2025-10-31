#!/usr/bin/env python3
"""
TradingView MCP Server - WORKING VERSION
Uses Playwright for lightweight browser automation (required because TradingView renders charts client-side).
Optimized with browser reuse and cookie-based authentication for minimal resource usage.
"""

import os
import base64
import logging
import asyncio
from typing import Optional
from pathlib import Path

from dotenv import load_dotenv
from playwright.async_api import async_playwright, Browser, BrowserContext
from mcp.server import Server
from mcp.types import Tool, TextContent, ImageContent
from mcp.server.stdio import stdio_server

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Global browser instance (reused for efficiency)
_playwright = None
_browser: Optional[Browser] = None
_context: Optional[BrowserContext] = None


async def get_browser_context() -> BrowserContext:
    """Get or create a persistent browser context with TradingView authentication."""
    global _playwright, _browser, _context
    
    if _context is not None:
        return _context
    
    session_id = os.getenv("TRADINGVIEW_SESSION_ID")
    session_id_sign = os.getenv("TRADINGVIEW_SESSION_ID_SIGN")
    
    if not session_id or not session_id_sign:
        raise ValueError("TradingView credentials not found in environment")
    
    # Start Playwright
    if _playwright is None:
        _playwright = await async_playwright().start()
    
    # Launch browser in headless mode (lightweight)
    if _browser is None:
        _browser = await _playwright.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--no-first-run',
                '--no-zygote',
                '--disable-gpu'
            ]
        )
        logger.info("Browser launched successfully")
    
    # Create context with cookies
    _context = await _browser.new_context(
        viewport={'width': 1920, 'height': 1080},
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    )
    
    # Add TradingView cookies
    await _context.add_cookies([
        {
            'name': 'sessionid',
            'value': session_id,
            'domain': '.tradingview.com',
            'path': '/',
            'httpOnly': True,
            'secure': True,
            'sameSite': 'Lax'
        },
        {
            'name': 'sessionid_sign',
            'value': session_id_sign,
            'domain': '.tradingview.com',
            'path': '/',
            'httpOnly': True,
            'secure': True,
            'sameSite': 'Lax'
        }
    ])
    
    logger.info("Browser context created with authentication")
    return _context


async def get_chart_snapshot(
    symbol: str,
    interval: str = "D",
    width: int = 1200,
    height: int = 600,
    theme: str = "dark"
) -> Optional[bytes]:
    """
    Fetch a TradingView chart snapshot.
    
    Args:
        symbol: Trading symbol (e.g., "BINANCE:BTCUSDT")
        interval: Chart interval (1, 5, 15, 30, 60, 240, D, W, M)
        width: Image width
        height: Image height
        theme: Chart theme (dark or light)
    
    Returns:
        PNG image bytes or None if failed
    """
    try:
        context = await get_browser_context()
        page = await context.new_page()
        
        # Set viewport
        await page.set_viewport_size({"width": width, "height": height})
        
        # Build TradingView chart URL
        chart_url = (
            f"https://www.tradingview.com/chart/?symbol={symbol}"
            f"&interval={interval}"
            f"&theme={theme}"
        )
        
        logger.info(f"Loading chart: {symbol} ({interval})")
        
        # Navigate to chart with longer timeout
        try:
            await page.goto(chart_url, wait_until="domcontentloaded", timeout=45000)
        except:
            # Fallback: try without waiting for full network idle
            await page.goto(chart_url, timeout=45000)
        
        # Wait for chart to load (with fallback)
        try:
            await page.wait_for_selector('div[data-name="legend-source-item"]', timeout=20000)
        except:
            # Alternative selector if the first one doesn't work
            try:
                await page.wait_for_selector('.chart-container', timeout=10000)
            except:
                pass  # Continue anyway
        
        # Additional wait for chart rendering
        await asyncio.sleep(3)
        
        # Take screenshot
        screenshot = await page.screenshot(type='png', full_page=False)
        
        await page.close()
        logger.info(f"Screenshot captured: {len(screenshot)} bytes")
        
        return screenshot
        
    except Exception as e:
        logger.error(f"Failed to capture chart: {e}")
        return None


async def validate_session() -> bool:
    """Validate if TradingView session is working."""
    try:
        context = await get_browser_context()
        page = await context.new_page()
        
        await page.goto("https://www.tradingview.com/", timeout=15000)
        
        # Check if we're logged in (look for user menu or profile indicators)
        await asyncio.sleep(1)
        content = await page.content()
        
        await page.close()
        
        # If we see login/signin, we're NOT authenticated
        is_authenticated = 'sign in' not in content.lower() or 'user-menu' in content.lower()
        
        return is_authenticated
        
    except Exception as e:
        logger.error(f"Session validation failed: {e}")
        return False


async def cleanup():
    """Cleanup browser resources."""
    global _browser, _context, _playwright
    
    if _context:
        await _context.close()
        _context = None
    
    if _browser:
        await _browser.close()
        _browser = None
    
    if _playwright:
        await _playwright.stop()
        _playwright = None


# Initialize MCP server
app = Server("tradingview-mcp")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available MCP tools."""
    return [
        Tool(
            name="get_chart_snapshot",
            description="Fetch a TradingView chart snapshot for a given symbol and timeframe. "
                       "Returns the chart as a base64-encoded PNG image. "
                       "Symbol format: 'EXCHANGE:SYMBOL' (e.g., 'BINANCE:BTCUSDT', 'NASDAQ:AAPL'). "
                       "Timeframes: 1, 5, 15, 30, 60, 240 (minutes) or D, W, M (day/week/month).",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Trading symbol in TradingView format (e.g., 'BINANCE:BTCUSDT')"
                    },
                    "interval": {
                        "type": "string",
                        "description": "Chart interval: 1, 5, 15, 30, 60, 240 (minutes) or D, W, M",
                        "default": "D"
                    },
                    "width": {
                        "type": "number",
                        "description": "Image width in pixels (default: 1200)",
                        "default": 1200
                    },
                    "height": {
                        "type": "number",
                        "description": "Image height in pixels (default: 600)",
                        "default": 600
                    },
                    "theme": {
                        "type": "string",
                        "description": "Chart theme: 'dark' or 'light' (default: dark)",
                        "default": "dark",
                        "enum": ["dark", "light"]
                    }
                },
                "required": ["symbol"]
            }
        ),
        Tool(
            name="validate_session",
            description="Validate if the TradingView session credentials are working correctly.",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="list_timeframes",
            description="List all available timeframes/intervals for TradingView charts.",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent | ImageContent]:
    """Handle tool calls."""
    
    # Check credentials
    session_id = os.getenv("TRADINGVIEW_SESSION_ID")
    session_id_sign = os.getenv("TRADINGVIEW_SESSION_ID_SIGN")
    
    if not session_id or not session_id_sign:
        return [TextContent(
            type="text",
            text="Error: TradingView credentials not found. Please set TRADINGVIEW_SESSION_ID and "
                 "TRADINGVIEW_SESSION_ID_SIGN in your .env file."
        )]
    
    if name == "validate_session":
        is_valid = await validate_session()
        status = "✓ Valid" if is_valid else "✗ Invalid"
        return [TextContent(
            type="text",
            text=f"Session Status: {status}\n\n"
                 f"The TradingView session credentials are {'working correctly' if is_valid else 'not working'}."
        )]
    
    elif name == "list_timeframes":
        timeframes = {
            "Minutes": ["1", "5", "15", "30", "60", "240"],
            "Days/Weeks/Months": ["D", "W", "M"]
        }
        
        result = "Available TradingView Timeframes:\n\n"
        for category, intervals in timeframes.items():
            result += f"{category}:\n"
            for interval in intervals:
                result += f"  - {interval}\n"
        
        result += "\nExamples:\n"
        result += "  - '5' = 5-minute chart\n"
        result += "  - '60' = 1-hour chart\n"
        result += "  - 'D' = Daily chart\n"
        
        return [TextContent(type="text", text=result)]
    
    elif name == "get_chart_snapshot":
        symbol = arguments.get("symbol")
        interval = arguments.get("interval", "D")
        width = int(arguments.get("width", 1200))
        height = int(arguments.get("height", 600))
        theme = arguments.get("theme", "dark")
        
        if not symbol:
            return [TextContent(
                type="text",
                text="Error: 'symbol' parameter is required. Example: 'BINANCE:BTCUSDT'"
            )]
        
        logger.info(f"Fetching chart snapshot for {symbol} ({interval})")
        
        # Get the chart snapshot
        image_data = await get_chart_snapshot(symbol, interval, width, height, theme)
        
        if image_data:
            # Encode as base64
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            
            return [
                TextContent(
                    type="text",
                    text=f"Chart snapshot for {symbol} (Interval: {interval})\n"
                         f"Size: {width}x{height} | Theme: {theme}\n"
                         f"Image size: {len(image_data)} bytes"
                ),
                ImageContent(
                    type="image",
                    data=image_base64,
                    mimeType="image/png"
                )
            ]
        else:
            return [TextContent(
                type="text",
                text=f"Failed to fetch chart snapshot for {symbol}.\n\n"
                     f"Possible reasons:\n"
                     f"1. Invalid symbol format (use 'EXCHANGE:SYMBOL' format)\n"
                     f"2. Symbol not found on TradingView\n"
                     f"3. Network or timeout issues\n\n"
                     f"Please check your input and try again."
            )]
    
    return [TextContent(type="text", text=f"Unknown tool: {name}")]


async def main():
    """Run the MCP server."""
    logger.info("Starting TradingView MCP Server with Playwright...")
    
    # Validate environment variables
    if not os.getenv("TRADINGVIEW_SESSION_ID") or not os.getenv("TRADINGVIEW_SESSION_ID_SIGN"):
        logger.warning(
            "Warning: TradingView credentials not found in environment. "
            "Please set TRADINGVIEW_SESSION_ID and TRADINGVIEW_SESSION_ID_SIGN in .env file."
        )
    
    try:
        async with stdio_server() as (read_stream, write_stream):
            await app.run(read_stream, write_stream, app.create_initialization_options())
    finally:
        await cleanup()


if __name__ == "__main__":
    asyncio.run(main())
