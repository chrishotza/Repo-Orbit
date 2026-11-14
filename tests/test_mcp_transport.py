"""Synthetic stdio transport tests: no network or full-corpus mutation."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import unittest

from repoorbit.mcp import MAX_RPC_LINE_BYTES

ROOT = Path(__file__).resolve().parents[1]


def request_lines(payloads: list[bytes]) -> list[dict]:
    completed = subprocess.run(
        [sys.executable, "-m", "repoorbit.mcp"],
        cwd=ROOT,
        input=b"".join(payloads),
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        timeout=15, check=True,
    )
    return [json.loads(row) for row in completed.stdout.splitlines()]


def ping(identifier: int) -> bytes:
    return (json.dumps({"jsonrpc": "2.0", "id": identifier,
                        "method": "ping"}) + "\n").encode("utf-8")


class BoundedTransportTests(unittest.TestCase):
    def test_valid_messages_still_work_and_keep_request_ids(self):
        replies = request_lines([ping(7), ping(8)])
        self.assertEqual([row["id"] for row in replies], [7, 8])
        self.assertTrue(all(row["result"] == {} for row in replies))

    def test_oversized_message_is_drained_and_following_request_is_processed(self):
        # The large JSON-RPC ID crosses several bounded read chunks before
        # the newline. A partial message must never be interpreted as the next.
        huge = (
            b'{"jsonrpc":"2.0","id":"' +
            b"x" * (MAX_RPC_LINE_BYTES * 3 + 3) +
            b'","method":"ping"}\n'
        )
        replies = request_lines([huge, ping(9)])
        self.assertEqual(len(replies), 2)
        self.assertIsNone(replies[0]["id"])
        self.assertEqual(replies[0]["error"]["code"], -32600)
        self.assertEqual(replies[1]["id"], 9)
        self.assertEqual(replies[1]["result"], {})

    def test_duplicate_json_keys_are_rejected_before_dispatch(self):
        request = (
            b'{"jsonrpc":"2.0","id":7,"method":"ping",'
            b'"method":"tools/list"}\n'
        )
        replies = request_lines([request, ping(10)])
        self.assertEqual(replies[0]["error"]["code"], -32700)
        self.assertEqual(replies[1]["id"], 10)

    def test_nonstandard_constants_and_broken_utf8_are_rejected(self):
        for invalid in (
            b'{"jsonrpc":"2.0","id":NaN,"method":"ping"}\n',
            b'{"jsonrpc":"2.0","id":Infinity,"method":"ping"}\n',
            b'{"jsonrpc":"2.0","id":1,"method":"ping","params":{"v":-Infinity}}\n',
            b'{"jsonrpc":"2.0","id":1,"method":"ping"}\xff\n',
        ):
            with self.subTest(invalid=invalid[:45]):
                result = request_lines([invalid, ping(11)])
                self.assertEqual(result[0]["error"]["code"], -32700)
                self.assertEqual(result[1]["id"], 11)

    def test_duplicate_nested_parameter_keys_are_rejected(self):
        invalid = (
            b'{"jsonrpc":"2.0","id":1,"method":"tools/call",'
            b'"params":{"name":"search","arguments":{"q":"python","q":"go"}}}\n'
        )
        replies = request_lines([invalid])
        self.assertEqual(replies[0]["error"]["code"], -32700)
        self.assertIsNone(replies[0]["id"])

    def test_protocol_errors_do_not_echo_untrusted_values(self):
        secret = "private-token-should-not-appear"
        invalid = ('{"jsonrpc":"2.0","id":"' + secret + '",'
                   '"method":"ping","method":"ping"}\n').encode("utf-8")
        replies = request_lines([invalid])
        self.assertEqual(replies[0]["error"]["message"], "Parse error")
        self.assertNotIn(secret, json.dumps(replies))


if __name__ == "__main__":
    unittest.main()
