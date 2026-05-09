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
| Tier | Price | Limits |
|------|-------|--------|
| Free | $0 | 50 queries/month |
| Pro | $19/mo | Unlimited |
| Enterprise | Custom | Custom data, SLA |

[Subscribe to Pro →](https://buy.stripe.com/28EbJ36PlgAk5zG3IL1oI0l)

## Subscription
Pro subscribers get unlimited queries, priority support, and CSV export support.
Subscribe at: https://buy.stripe.com/28EbJ36PlgAk5zG3IL1oI0l

Data sourced from SEC EDGAR XBRL (public domain).
