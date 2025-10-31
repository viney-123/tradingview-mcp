# Changelog

All notable changes to this project will be documented in this file.

## [0.1.0] - 2025-10-31

### Added
- Initial release with Playwright-based chart fetching
- Three MCP tools: `get_chart_snapshot`, `validate_session`, `list_timeframes`
- Session-based authentication via TradingView cookies
- Support for all TradingView symbols and timeframes
- Persistent browser reuse for efficiency
- Comprehensive documentation in README.md

### Technical Details
- Uses Playwright in headless mode (~150MB memory)
- Optimized with browser instance reuse
- Response time: 3-5 seconds per chart
- Supports customizable dimensions and themes

[0.1.0]: https://github.com/yourusername/tradingview-mcp/releases/tag/v0.1.0
