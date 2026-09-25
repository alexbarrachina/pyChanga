"""Source-aware Python errors shared by workers and runtime clients."""
import traceback


def error_info(error: BaseException, filename: str) -> dict:
    """Keep the user's source location and a bounded traceback for any client."""
    frames = traceback.extract_tb(error.__traceback__)
    frame = next((frame for frame in reversed(frames) if frame.filename == filename), None)
    return {
        "message": f"{type(error).__name__}: {error}",
        "filename": filename,
        "line": getattr(error, "lineno", None) or (frame.lineno if frame else 1),
        "column": getattr(error, "offset", None) or 1,
        "traceback": "".join(traceback.format_exception(error))[-16000:],
    }
