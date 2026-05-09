#!/usr/bin/env python3
"""
SEC EDGAR MCP Server — Financial Data for AI Agents.

Provides MCP tools for searching and retrieving SEC EDGAR financial data,
including income statements, balance sheets, cash flow statements, and
financial ratios for 10,000+ US public companies.

Usage:
    python3 sec_mcp.py                   # stdio mode (for MCP clients)
    python3 sec_mcp.py --http 8080       # HTTP mode (for testing)
"""

import json
import sys
import os
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sources.sec_edgar import SECClient


def handle_mcp_request(request: dict, client: SECClient) -> dict:
    """Process a single MCP JSON-RPC request."""
    method = request.get("method", "")
    params = request.get("params", {}) or {}
    req_id = request.get("id")

    try:
        if method == "list_tools":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "tools": [
                        {
                            "name": "search_company",
                            "description": "Search for a US public company by ticker symbol or company name. Returns ticker, full name, CIK, and match type.",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "query": {"type": "string", "description": "Ticker symbol (e.g., 'AAPL', 'NVDA', 'MSFT') or company name (e.g., 'Apple', 'NVIDIA')"},
                                },
                                "required": ["query"],
                            },
                        },
                        {
                            "name": "get_company_facts",
                            "description": "List all available US GAAP financial facts for a company. Returns fact names you can use with get_financial_fact.",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "ticker": {"type": "string", "description": "Stock ticker symbol (e.g., 'AAPL', 'NVDA', 'MSFT')"},
                                },
                                "required": ["ticker"],
                            },
                        },
                        {
                            "name": "get_financial_fact",
                            "description": "Get a specific financial fact for a company. Supports 503+ US GAAP facts including Revenues, NetIncomeLoss, Assets, Liabilities, CashAndCashEquivalentsAtCarryingValue, OperatingCashFlow, etc.",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "ticker": {"type": "string", "description": "Stock ticker symbol"},
                                    "fact_name": {"type": "string", "description": "US GAAP fact name (e.g., 'Revenues', 'NetIncomeLoss', 'Assets', 'OperatingCashFlow'). Use get_company_facts to see all available."},
                                    "limit": {"type": "integer", "description": "Max number of historical values to return", "default": 5},
                                },
                                "required": ["ticker", "fact_name"],
                            },
                        },
                        {
                            "name": "get_income_statement",
                            "description": "Get the income statement for a company. Returns revenues, costs, gross profit, operating expenses, net income, and EPS across multiple periods.",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "ticker": {"type": "string", "description": "Stock ticker symbol"},
                                    "periods": {"type": "integer", "description": "Number of historical periods to return", "default": 3},
                                },
                                "required": ["ticker"],
                            },
                        },
                        {
                            "name": "get_balance_sheet",
                            "description": "Get the balance sheet for a company. Returns assets (current, cash, receivables, PPE), liabilities (current, long-term debt), and equity.",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "ticker": {"type": "string", "description": "Stock ticker symbol"},
                                    "periods": {"type": "integer", "description": "Number of historical periods to return", "default": 3},
                                },
                                "required": ["ticker"],
                            },
                        },
                        {
                            "name": "get_cash_flow",
                            "description": "Get the cash flow statement for a company. Returns operating, investing, and financing cash flows.",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "ticker": {"type": "string", "description": "Stock ticker symbol"},
                                    "periods": {"type": "integer", "description": "Number of historical periods to return", "default": 3},
                                },
                                "required": ["ticker"],
                            },
                        },
                        {
                            "name": "get_financial_ratios",
                            "description": "Calculate key financial ratios for a company. Returns net profit margin, return on equity, debt-to-equity ratio, and EPS.",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "ticker": {"type": "string", "description": "Stock ticker symbol"},
                                },
                                "required": ["ticker"],
                            },
                        },
                        {
                            "name": "get_recent_filings",
                            "description": "Get recent SEC filings (10-K, 10-Q, 8-K) for a company. Returns form type, filing date, and report date.",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "ticker": {"type": "string", "description": "Stock ticker symbol"},
                                    "limit": {"type": "integer", "description": "Max filings to return", "default": 10},
                                },
                                "required": ["ticker"],
                            },
                        },
                    ],
                },
            }

        elif method == "call_tool":
            tool_name = params.get("name", "")
            args = params.get("arguments", {}) or {}

            handlers = {
                "search_company": lambda: client.search_company(args.get("query", "")),
                "get_company_facts": lambda: client.get_company_facts(args.get("ticker", "")),
                "get_financial_fact": lambda: client.get_financial_fact(
                    args.get("ticker", ""),
                    args.get("fact_name", ""),
                    limit=args.get("limit", 5),
                ),
                "get_income_statement": lambda: client.get_income_statement(
                    args.get("ticker", ""),
                    limit=args.get("periods", 3),
                ),
                "get_balance_sheet": lambda: client.get_balance_sheet(
                    args.get("ticker", ""),
                    limit=args.get("periods", 3),
                ),
                "get_cash_flow": lambda: client.get_cash_flow(
                    args.get("ticker", ""),
                    limit=args.get("periods", 3),
                ),
                "get_financial_ratios": lambda: client.get_financial_ratios(args.get("ticker", "")),
                "get_recent_filings": lambda: client.get_recent_filings(
                    args.get("ticker", ""),
                    limit=args.get("limit", 10),
                ),
            }

            if tool_name in handlers:
                result = handlers[tool_name]()
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [{"type": "text", "text": json.dumps(result, indent=2, default=str)}],
                    },
                }
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32601, "message": f"Tool not found: {tool_name}"},
                }

        elif method == "ping":
            return {"jsonrpc": "2.0", "id": req_id, "result": {"status": "ok"}}

        else:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32601, "message": f"Method not found: {method}"},
            }

    except Exception as e:
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32603, "message": f"Internal error: {str(e)}"},
        }


def run_stdio():
    """Run MCP server in stdio mode."""
    client = SECClient()

    # Server info
    info = {
        "jsonrpc": "2.0",
        "method": "server/info",
        "params": {
            "name": "sec-edgar-mcp",
            "version": "1.0.0",
            "description": "SEC EDGAR financial data for AI agents. Income statements, balance sheets, cash flow, ratios for 10,000+ US public companies.",
        },
    }
    print(json.dumps(info), flush=True)

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
            response = handle_mcp_request(request, client)
            print(json.dumps(response), flush=True)
        except json.JSONDecodeError:
            error = {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "Parse error"}}
            print(json.dumps(error), flush=True)
        except Exception as e:
            error = {"jsonrpc": "2.0", "id": None, "error": {"code": -32603, "message": str(e)}}
            print(json.dumps(error), flush=True)


def run_http_test(port: int = 8081):
    """Run HTTP test server."""
    from http.server import HTTPServer, BaseHTTPRequestHandler

    class Handler(BaseHTTPRequestHandler):
        client = SECClient()

        def do_GET(self):
            if self.path == "/health":
                self.send(200, {"status": "ok", "name": "sec-edgar-mcp", "version": "1.0.0"})
            elif self.path == "/tools":
                req = {"jsonrpc": "2.0", "id": 1, "method": "list_tools"}
                resp = handle_mcp_request(req, self.client)
                self.send(200, resp)
            else:
                self.send(404, {"error": "not found"})

        def do_POST(self):
            content_len = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_len)
            try:
                req = json.loads(body)
                resp = handle_mcp_request(req, self.client)
                self.send(200, resp)
            except Exception as e:
                self.send(500, {"error": str(e)})

        def send(self, code, data):
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(data).encode())

        def log_message(self, format, *args):
            pass

    server = HTTPServer(("0.0.0.0", port), Handler)
    print(f"HTTP test server on http://localhost:{port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SEC EDGAR MCP Server")
    parser.add_argument("--http", type=int, help="Run in HTTP mode on given port")
    args = parser.parse_args()
    if args.http:
        run_http_test(args.http)
    else:
        run_stdio()
