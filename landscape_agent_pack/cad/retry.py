"""Bounded retries for idempotent COM reads only. Never retry entity creation."""
from dataclasses import dataclass
import time

BUSY_HRESULTS = {-2147418111, -2147417846}  # CALL_REJECTED, SERVERCALL_RETRYLATER
RPC_UNAVAILABLE = {-2147023174, -2147417848, -2147418113}


class CadComError(RuntimeError):
    pass


class ComBusyTimeout(CadComError):
    pass


class ComDisconnected(CadComError):
    pass


def hresult(exc):
    value = getattr(exc, "hresult", None)
    if value is None and getattr(exc, "args", None):
        value = exc.args[0]
    return value if isinstance(value, int) else None


@dataclass(frozen=True)
class RetryPolicy:
    max_attempts: int = 8
    delay: float = 0.2
    backoff: float = 1.4
    timeout: float = 8.0
    retryable_error_set: frozenset[int] = frozenset(BUSY_HRESULTS)


def read_with_retry(fn, policy=RetryPolicy()):
    if policy.max_attempts < 1 or policy.timeout <= 0:
        raise ValueError("Invalid retry policy")
    started = time.monotonic()
    for attempt in range(policy.max_attempts):
        try:
            return fn()
        except Exception as exc:
            code = hresult(exc)
            if code in RPC_UNAVAILABLE:
                raise ComDisconnected(f"COM disconnected HRESULT={code}") from exc
            transient_wrapper = isinstance(exc, AttributeError) and "<unknown>" in str(exc)
            if code not in policy.retryable_error_set and not transient_wrapper:
                raise
            elapsed = time.monotonic() - started
            remaining = policy.timeout - elapsed
            if attempt + 1 >= policy.max_attempts or remaining <= 0:
                raise ComBusyTimeout(f"COM read busy after {attempt + 1} attempts; HRESULT={code}") from exc
            time.sleep(min(policy.delay * policy.backoff ** attempt, remaining))
