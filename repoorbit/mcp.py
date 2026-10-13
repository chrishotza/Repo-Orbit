"""Minimal MCP stdio tool server (newline-delimited JSON-RPC 2.0).

Standard library only. No tokens, network, paid APIs or human prompts required
at runtime. The MCP host launches this automatically when configured.
"""
from __future__ import annotations

import json
import sys

from . import __version__
from .agent import call

PROTOCOL_VERSION = "2025-06-18"

TOOLS = [
    {
        "name": "search",
        "description": "Deterministic offline repo lookup. Compact results; not a functional or cost verification.",
        "inputSchema": {
            "type": "object", "required": ["q"], "additionalProperties": False,
            "properties": {
                "q": {"type": "string", "minLength": 1, "maxLength": 200},
                "limit": {"type": "integer", "minimum": 1, "maximum": 20, "default": 5},
                "offset": {"type": "integer", "minimum": 0, "maximum": 10000, "default": 0},
                "role": {"type": "string", "enum": ["catalog", "project", "reference"]}
            },
        },
    },
    {
        "name": "resolve",
        "description": "Exact repository lookup by slug, GitHub URL, or verified numeric ID (id:589831718); includes evidence without function/cost claims.",
        "inputSchema": {
            "type": "object", "required": ["repo"], "additionalProperties": False,
            "properties": {"repo": {"type": "string", "minLength": 3, "maxLength": 240}},
        },
    },
    {
        "name": "recommend",
        "description": "EN/ES task-to-repository suggestions backed by upstream README snapshots. Cost and execution UNVERIFIED. strict_free=True returns no results without independent free evidence.",
        "inputSchema": {
            "type": "object", "required": ["q"], "additionalProperties": False,
            "properties": {
                "q": {"type": "string", "minLength": 1, "maxLength": 200},
                "limit": {"type": "integer", "minimum": 1, "maximum": 10, "default": 5},
                "strict_free": {"type": "boolean", "default": False}
            },
        },
    },
    {
        "name": "categories",
        "description": "List subject categories with exact corpus counts. Editorial/keyword hints, NOT validated capabilities.",
        "inputSchema": {"type": "object", "additionalProperties": False},
    },
    {
        "name": "classify",
        "description": "Explain one repository subject label, whether editorial, lexical hint or unknown; not a functionality test.",
        "inputSchema": {
            "type": "object", "required": ["repo"], "additionalProperties": False,
            "properties": {"repo": {"type": "string", "minLength": 3, "maxLength": 240}},
        },
    },
    {
        "name": "browse",
        "description": "Bounded category navigation with explicit uncertain classification and existence filter.",
        "inputSchema": {
            "type": "object", "required": ["category"], "additionalProperties": False,
            "properties": {
                "category": {"type": "string", "minLength": 3, "maxLength": 60},
                "limit": {"type": "integer", "minimum": 1, "maximum": 20, "default": 5},
                "offset": {"type": "integer", "minimum": 0, "maximum": 10000, "default": 0},
                "verified_only": {"type": "boolean", "default": False},
                "source": {"type": "string", "maxLength": 120},
            },
        },
    },
    {
        "name": "stats",
        "description": "Compact inventory counts; never implies complete coverage of GitHub.",
        "inputSchema": {"type": "object", "additionalProperties": False},
    },
]


def dispatch(message: dict) -> dict | None:
    """Process one MCP JSON-RPC message; return None for notifications."""
    if not isinstance(message, dict) or message.get("jsonrpc") != "2.0":
        return {"jsonrpc": "2.0", "id": None, "error": {"code": -32600, "message": "Invalid Request"}}
    if "id" not in message:
        return None
    req_id = message["id"]
    method = message.get("method")
    params = message.get("params") or {}
    if not isinstance(params, dict):
        return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32602, "message": "Invalid params"}}
    if method == "initialize":
        return {
            "jsonrpc": "2.0", "id": req_id,
            "result": {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {"name": "repoorbit", "version": __version__},
                "instructions": "Use categories/browse for topical navigation, classify for one slug, recommend for documented tasks, and resolve for exact evidence. Lexical subject hints are NOT working software. No free execution claims.",
            }
        }
    if method == "ping":
        return {"jsonrpc": "2.0", "id": req_id, "result": {}}
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": TOOLS}}
    if method == "tools/call":
        name = params.get("name")
        arguments = params.get("arguments") or {}
        try:
            result = call(name, arguments)
            return {
                "jsonrpc": "2.0", "id": req_id,
                "result": {"content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False, separators=(",", ":"))}], "isError": False},
            }
        except (TypeError, ValueError) as exc:
            return {
                "jsonrpc": "2.0", "id": req_id,
                "result": {"content": [{"type": "text", "text": str(exc)}], "isError": True},
            }
    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": "Method not found"}}


def main() -> None:
    for line in sys.stdin:
        try:
            payload = json.loads(line)
            response = dispatch(payload)
        except (TypeError, ValueError, RecursionError) as exc:
            response = {
                "jsonrpc": "2.0", "id": None,
                "error": {"code": -32700, "message": "Parse error: " + str(exc)[:100]},
            }
        if response is not None:
            print(json.dumps(response, ensure_ascii=False, separators=(",", ":")), flush=True)


if __name__ == "__main__":
    main()
