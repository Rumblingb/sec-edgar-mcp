"""SEC EDGAR API client — wraps the free SEC EDGAR XBRL API.

Provides access to:
- Company ticker/CIK mapping
- Financial statements (income statement, balance sheet, cash flow)
- Company facts (503+ US GAAP facts per company)
- Recent SEC filings (10-K, 10-Q, 8-K)

No API key needed. Rate limit: 10 requests/second.
SEC requires User-Agent header with email.
"""

import httpx
import json
import time
from typing import Optional, Dict, Any, List
from datetime import datetime

SEC_BASE = "https://www.sec.gov"
DATA_BASE = "https://data.sec.gov"

class SECClient:
    """Client for the SEC EDGAR XBRL API."""

    def __init__(self):
        self.headers = {
            "User-Agent": "SECMCP/1.0 (Agent API for SEC data; mailto:vishar.rumbling@gmail.com)",
        }
        self._ticker_map = None
        self._last_request = 0.0

    def _rate_limit(self):
        """Ensure max 10 requests/second."""
        elapsed = time.time() - self._last_request
        if elapsed < 0.1:  # 100ms between requests
            time.sleep(0.1 - elapsed)
        self._last_request = time.time()

    def _get(self, url: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make a rate-limited GET request to SEC."""
        self._rate_limit()
        resp = httpx.get(url, headers=self.headers, params=params, timeout=15.0, follow_redirects=True)
        resp.raise_for_status()
        return resp.json()

    @property
    def ticker_map(self) -> Dict[str, Dict]:
        """Map of ticker -> {cik, title, ...} for all public companies."""
        if self._ticker_map is None:
            data = self._get(f"{SEC_BASE}/files/company_tickers.json")
            self._ticker_map = {}
            for key, val in data.items():
                ticker = val["ticker"].upper()
                self._ticker_map[ticker] = {
                    "cik": str(val["cik_str"]).zfill(10),
                    "title": val["title"],
                    "cik_int": val["cik_str"],
                }
        return self._ticker_map

    def search_company(self, query: str) -> List[Dict[str, Any]]:
        """Search for a company by ticker or name."""
        query = query.upper()
        results = []

        # Direct ticker match
        if query in self.ticker_map:
            entry = self.ticker_map[query]
            results.append({
                "ticker": query,
                "name": entry["title"],
                "cik": entry["cik"],
                "match_type": "exact_ticker",
            })

        # Name search (fuzzy)
        for ticker, entry in self.ticker_map.items():
            if query in entry["title"].upper() or query in ticker:
                results.append({
                    "ticker": ticker,
                    "name": entry["title"],
                    "cik": entry["cik"],
                    "match_type": "name" if query in entry["title"].upper() else "ticker_partial",
                })
                if len(results) >= 10:
                    break

        return results

    def get_company_facts(self, ticker: str) -> Dict[str, Any]:
        """Get all US GAAP facts for a company."""
        if ticker.upper() not in self.ticker_map:
            return {"error": f"Ticker not found: {ticker}"}

        cik = self.ticker_map[ticker.upper()]["cik"]
        url = f"{DATA_BASE}/api/xbrl/companyfacts/CIK{cik}.json"
        data = self._get(url)

        facts = data.get("facts", {}).get("us-gaap", {})
        return {
            "entity_name": data.get("entityName", ""),
            "cik": cik,
            "ticker": ticker.upper(),
            "total_facts": len(facts),
            "fact_names": list(facts.keys()),
        }

    def get_financial_fact(
        self, ticker: str, fact_name: str, limit: int = 5
    ) -> Dict[str, Any]:
        """Get a specific US GAAP financial fact for a company.

        Common fact names:
        - Revenues, CostOfRevenue, GrossProfit, OperatingExpenses
        - NetIncomeLoss, EarningsPerShareBasic
        - Assets, Liabilities, StockholdersEquity
        - AssetsCurrent, LiabilitiesCurrent
        - CashAndCashEquivalentsAtCarryingValue
        - AccountsPayableCurrent, AccountsReceivableNet
        - OperatingCashFlow, InvestingCashFlow, FinancingCashFlow
        - CommonStockSharesOutstanding
        """
        if ticker.upper() not in self.ticker_map:
            return {"error": f"Ticker not found: {ticker}"}

        cik = self.ticker_map[ticker.upper()]["cik"]
        url = f"{DATA_BASE}/api/xbrl/companyfacts/CIK{cik}.json"
        data = self._get(url)

        facts = data.get("facts", {}).get("us-gaap", {})
        if fact_name not in facts:
            return {
                "error": f"Fact '{fact_name}' not found. Available: {', '.join(list(facts.keys())[:20])}...",
            }

        fact_data = facts[fact_name]
        # Get the values (usually in USD)
        label = fact_data.get("label", fact_name)
        description = fact_data.get("description", "")
        units = fact_data.get("units", {})
        
        # Try USD first, then any unit
        values = []
        for unit_name, entries in units.items():
            for entry in entries[:limit]:
                values.append({
                    "value": entry.get("val"),
                    "unit": unit_name,
                    "end_date": entry.get("end"),
                    "start_date": entry.get("start", entry.get("end")),
                    "form": entry.get("form"),
                    "filed": entry.get("filed"),
                    "fiscal_year": entry.get("fy"),
                    "fiscal_period": entry.get("fp"),
                })

        return {
            "company": data.get("entityName", ""),
            "ticker": ticker.upper(),
            "fact": fact_name,
            "label": label,
            "description": description,
            "values": values,
            "count": len(values),
        }

    def get_recent_filings(self, ticker: str, limit: int = 10) -> Dict[str, Any]:
        """Get recent SEC filings for a company (10-K, 10-Q, 8-K, etc.)."""
        if ticker.upper() not in self.ticker_map:
            return {"error": f"Ticker not found: {ticker}"}

        cik = self.ticker_map[ticker.upper()]["cik"]
        url = f"{DATA_BASE}/submissions/CIK{cik}.json"
        data = self._get(url)

        filings = data.get("filings", {}).get("recent", {})
        results = []
        for i in range(min(limit, len(filings.get("form", [])))):
            results.append({
                "form": filings["form"][i],
                "description": filings.get("primaryDocument", [""])[i] if i < len(filings.get("primaryDocument", [])) else "",
                "date": filings.get("filingDate", [""])[i] if i < len(filings.get("filingDate", [])) else "",
                "report_date": filings.get("reportDate", [""])[i] if i < len(filings.get("reportDate", [])) else "",
            })

        return {
            "company": data.get("name", ""),
            "cik": cik,
            "ticker": ticker.upper(),
            "filings": results,
            "count": len(results),
        }

    def get_income_statement(self, ticker: str, limit: int = 5) -> Dict[str, Any]:
        """Get income statement (revenues, expenses, net income)."""
        facts_needed = [
            "Revenues", "CostOfRevenue", "GrossProfit",
            "OperatingExpenses", "OperatingIncomeLoss",
            "InterestExpense", "IncomeTaxExpenseBenefit",
            "NetIncomeLoss", "EarningsPerShareBasic",
        ]
        result = {"company": "", "ticker": ticker.upper(), "items": {}}
        for fact in facts_needed:
            try:
                data = self.get_financial_fact(ticker, fact, limit=limit)
                if "error" not in data:
                    result["company"] = data["company"]
                    result["items"][fact] = {
                        "label": data.get("label", fact),
                        "values": data.get("values", []),
                    }
            except:
                pass
        return result

    def get_balance_sheet(self, ticker: str, limit: int = 5) -> Dict[str, Any]:
        """Get balance sheet (assets, liabilities, equity)."""
        facts_needed = [
            "Assets", "AssetsCurrent", "CashAndCashEquivalentsAtCarryingValue",
            "AccountsReceivableNet", "InventoryNet",
            "PropertyPlantAndEquipmentNet",
            "Liabilities", "LiabilitiesCurrent", "AccountsPayableCurrent",
            "LongTermDebtNoncurrent", "StockholdersEquity",
        ]
        result = {"company": "", "ticker": ticker.upper(), "items": {}}
        for fact in facts_needed:
            try:
                data = self.get_financial_fact(ticker, fact, limit=limit)
                if "error" not in data:
                    result["company"] = data["company"]
                    result["items"][fact] = {
                        "label": data.get("label", fact),
                        "values": data.get("values", []),
                    }
            except:
                pass
        return result

    def get_cash_flow(self, ticker: str, limit: int = 5) -> Dict[str, Any]:
        """Get cash flow statement (operating, investing, financing)."""
        facts_needed = [
            "NetCashProvidedByUsedInOperatingActivities",
            "NetCashProvidedByUsedInInvestingActivities",
            "NetCashProvidedByUsedInFinancingActivities",
            "CashAndCashEquivalentsAtCarryingValue",
        ]
        result = {"company": "", "ticker": ticker.upper(), "items": {}}
        for fact in facts_needed:
            try:
                data = self.get_financial_fact(ticker, fact, limit=limit)
                if "error" not in data:
                    result["company"] = data["company"]
                    result["items"][fact] = {
                        "label": data.get("label", fact),
                        "values": data.get("values", []),
                    }
            except:
                pass
        return result

    def get_financial_ratios(self, ticker: str) -> Dict[str, Any]:
        """Calculate key financial ratios from available data."""
        result = {"company": "", "ticker": ticker.upper(), "ratios": {}}

        try:
            # Get key financial data
            revenues = self.get_financial_fact(ticker, "Revenues", limit=2)
            net_income = self.get_financial_fact(ticker, "NetIncomeLoss", limit=2)
            assets = self.get_financial_fact(ticker, "Assets", limit=2)
            equity = self.get_financial_fact(ticker, "StockholdersEquity", limit=2)
            shares = self.get_financial_fact(ticker, "CommonStockSharesOutstanding", limit=2)

            if "error" not in revenues and revenues.get("values"):
                result["company"] = revenues.get("company", "")
                rev = revenues["values"][0]["value"] if revenues["values"] else 0
                ni = net_income["values"][0]["value"] if "error" not in net_income and net_income.get("values") else 0
                a = assets["values"][0]["value"] if "error" not in assets and assets.get("values") else 0
                e = equity["values"][0]["value"] if "error" not in equity and equity.get("values") else 0
                s = shares["values"][0]["value"] if "error" not in shares and shares.get("values") else 0

                result["ratios"] = {
                    "net_profit_margin": round(ni / rev * 100, 2) if rev else None,
                    "return_on_equity": round(ni / e * 100, 2) if e else None,
                    "debt_to_equity": round((a - e) / e, 2) if e else None,
                    "eps": round(ni / s, 2) if s else None,
                }

        except Exception as e:
            result["error"] = str(e)

        return result
