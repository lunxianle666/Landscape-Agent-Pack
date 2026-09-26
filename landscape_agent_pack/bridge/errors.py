class BridgeError(RuntimeError):
    """A Bridge request failed with a known, non-successful outcome."""


class BlockedNativeImport(BridgeError):
    """SketchUp's native CAD importer is unavailable or rejected the input."""


class OutcomeUnknown(BridgeError):
    """A submitted mutation may have executed; inspect model before retrying."""
