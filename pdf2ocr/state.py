"""Global state management for pdf2ocr."""

import threading

# Thread-safe event for graceful shutdown
shutdown_requested = threading.Event()


# Function to check shutdown state
def is_shutdown_requested():
    """Check if shutdown has been requested.

    Returns:
        bool: True if shutdown was requested
    """
    return shutdown_requested.is_set()


# Function to request shutdown
def request_shutdown():
    """Request a graceful shutdown."""
    shutdown_requested.set()


# Function to force exit
def force_exit():
    """Force immediate shutdown."""
    request_shutdown()
