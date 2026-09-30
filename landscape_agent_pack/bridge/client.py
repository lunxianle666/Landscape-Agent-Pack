"""Bounded, authenticated Ringo protocol 3 client. Mutations are never replayed."""
import json
import math
import os
from pathlib import Path
import socket
import time
import uuid

from .errors import BridgeError, OutcomeUnknown

MAX_FRAME = 4 * 1024 * 1024


class RingoClient:
    def __init__(self, config_path=None, *, timeout=30, connect_timeout=5):
        if not all(math.isfinite(v) and v > 0 for v in (timeout, connect_timeout)):
            raise ValueError("Timeouts must be finite and positive")
        path = config_path or os.environ.get("SKETCHUP_MCP_CONFIG")
        if not path:
            path = Path(os.environ.get("APPDATA", Path.home())) / "RingoSketchUpMCP" / "config.json"
        config = json.loads(Path(path).read_text(encoding="utf-8-sig"))
        self.host = config.get("host", "127.0.0.1")
        self.port = int(os.environ.get("SKETCHUP_PORT", config["port"]))
        self._token = os.environ.get("SKETCHUP_TOKEN", config.get("token", ""))
        if self.host != "127.0.0.1" or not 1 <= self.port <= 65535 or len(self._token) < 32:
            raise ValueError("Invalid local bridge configuration")
        self.timeout, self.connect_timeout = timeout, connect_timeout
        self.history = []  # Request IDs/methods/results only; never token or code.
        self.sock = None
        self.buffer = b""

    def connect(self):
        if self.sock is not None:
            return
        try:
            self.sock = socket.create_connection((self.host, self.port), self.connect_timeout)
            hello = self.call("bridge.hello", {"protocol": 3})
            if hello.get("protocol") != 3 or not isinstance(hello.get("capabilities"), dict):
                raise BridgeError("Incompatible or invalid bridge handshake")
            self.hello = hello
        except Exception:
            self.close()
            raise

    def close(self):
        if self.sock:
            self.sock.close()
        self.sock = None
        self.buffer = b""

    def call(self, method, params=None, *, mutation=False, deadline_ms=None):
        if self.sock is None:
            self.connect()
        request_id = uuid.uuid4().hex
        request = {"jsonrpc": "2.0", "id": request_id, "method": method,
                   "params": params or {}, "token": self._token,
                   "deadline_ms": deadline_ms if deadline_ms is not None else int((time.time() + self.timeout) * 1000)}
        wire = (json.dumps(request, ensure_ascii=False) + "\n").encode("utf-8")
        if len(wire) > MAX_FRAME:
            raise ValueError("Bridge request exceeds 4 MiB")
        row = {"id": request_id, "method": method, "mutation": mutation, "outcome": "pending"}
        self.history.append(row)
        started = time.monotonic()
        submitted = False
        try:
            self.sock.settimeout(self.timeout)
            submitted = True  # Partial send also makes a mutation uncertain.
            self.sock.sendall(wire)
            while b"\n" not in self.buffer:
                remaining = self.timeout - (time.monotonic() - started)
                if remaining <= 0:
                    raise TimeoutError()
                self.sock.settimeout(remaining)
                chunk = self.sock.recv(65536)
                if not chunk:
                    raise ConnectionError("Bridge disconnected")
                self.buffer += chunk
                if len(self.buffer) > MAX_FRAME:
                    raise BridgeError("Bridge response exceeds 4 MiB")
            line, self.buffer = self.buffer.split(b"\n", 1)
            response = json.loads(line.decode("utf-8"))
            if response.get("jsonrpc") != "2.0" or response.get("id") != request_id or ("result" in response) == ("error" in response):
                raise BridgeError("Invalid or mismatched bridge response")
            if "error" in response:
                error = response["error"]
                row.update(outcome="rejected", code=error.get("code"))
                raise BridgeError(f"Bridge error {error.get('code')}: {error.get('message')}")
            row["outcome"] = "completed"
            return response["result"]
        except (OSError, ValueError, BridgeError) as exc:
            rejected = row["outcome"] == "rejected"
            if not rejected:
                row["outcome"] = "unknown" if mutation and submitted else "failed"
                self.close()
                if mutation and submitted:
                    raise OutcomeUnknown(f"Request {request_id} outcome unknown; inspect model before retrying") from exc
            raise
        finally:
            row["elapsed_ms"] = round((time.monotonic() - started) * 1000)

    def data(self, method, params=None, **kwargs):
        result = self.call(method, params, **kwargs)
        if not result.get("success") or not isinstance(result.get("data"), dict):
            raise BridgeError("Bridge did not return successful data")
        return result["data"]

    def ruby(self, code, *, model_id, mutation=False, transaction=None):
        return self.data("ruby.eval", {"code": code, "model_id": model_id,
                         "transaction": mutation if transaction is None else transaction,
                         "operation_name": "LAP Bridge"},
                         mutation=mutation)["result"]
