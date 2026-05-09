# SEC EDGAR MCP Server

Financial data for AI agents. Income statements, balance sheets, cash flow, and ratios for 10,000+ US public companies.

## Tools
- `search_company` — Find companies by ticker or name
- `get_income_statement` — Revenue, costs, net income
- `get_balance_sheet` — Assets, liabilities, equity
- `get_cash_flow` — Operating, investing, financing cash flows
- `get_financial_fact` — Any of 503+ US GAAP facts
- `get_financial_ratios` — Profit margin, ROE, debt/equity, EPS
- `get_recent_filings` — SEC filing history

## Usage
```bash
pip install httpx
python3 sec_mcp.py
```

## Pricing
- Free: 50 queries/month
- Pro: $19/mo — unlimited

Data sourced from SEC EDGAR XBRL (public domain).
