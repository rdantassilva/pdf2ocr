"""Tests for state.py module shutdown management functionality."""

import pytest
import threading
import time
from unittest.mock import patch, MagicMock
from pdf2ocr.state import (
    shutdown_requested,
    is_shutdown_requested,
    request_shutdown,
    force_exit
)


def test_initial_shutdown_state():
    """Test that shutdown is not requested initially."""
    # Reset state for clean test
    if shutdown_requested.is_set():
        shutdown_requested.clear()
    
    assert not is_shutdown_requested()
    assert not shutdown_requested.is_set()


def test_request_shutdown():
    """Test that request_shutdown sets the shutdown flag."""
    # Reset state for clean test
    if shutdown_requested.is_set():
        shutdown_requested.clear()
    
    # Initially not set
    assert not is_shutdown_requested()
    
    # Request shutdown
    request_shutdown()
    
    # Now should be set
    assert is_shutdown_requested()
    assert shutdown_requested.is_set()


def test_force_exit():
    """Test that force_exit calls request_shutdown."""
    # Reset state for clean test
    if shutdown_requested.is_set():
        shutdown_requested.clear()
    
    # Initially not set
    assert not is_shutdown_requested()
    
    # Force exit
    force_exit()
    
    # Should have triggered shutdown
    assert is_shutdown_requested()
    assert shutdown_requested.is_set()


def test_shutdown_thread_safety():
    """Test that shutdown management is thread-safe."""
    # Reset state for clean test
    if shutdown_requested.is_set():
        shutdown_requested.clear()
    
    results = []
    
    def worker_thread(thread_id):
        """Worker function that checks and sets shutdown."""
        # Check initial state
        initial_state = is_shutdown_requested()
        
        # Wait a bit to create race conditions
        time.sleep(0.01)
        
        # Request shutdown from this thread
        if thread_id == 0:
            request_shutdown()
        
        # Wait a bit more
        time.sleep(0.01)
        
        # Check final state
        final_state = is_shutdown_requested()
        
        results.append((thread_id, initial_state, final_state))
    
    # Create multiple threads
    threads = []
    for i in range(5):
        thread = threading.Thread(target=worker_thread, args=(i,))
        threads.append(thread)
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    # Verify results
    assert len(results) == 5
    
    # All threads should see the final state as shutdown requested
    for thread_id, initial, final in results:
        assert final  # All should see shutdown in the end
    
    # At least one thread (thread 0) should have seen the transition
    thread_0_result = next(r for r in results if r[0] == 0)
    assert not thread_0_result[1]  # Thread 0 should have seen initial state as False
    assert thread_0_result[2]      # Thread 0 should have seen final state as True


def test_multiple_shutdown_requests():
    """Test that multiple shutdown requests don't cause issues."""
    # Reset state for clean test
    if shutdown_requested.is_set():
        shutdown_requested.clear()
    
    # Initially not set
    assert not is_shutdown_requested()
    
    # Request shutdown multiple times
    request_shutdown()
    assert is_shutdown_requested()
    
    request_shutdown()
    assert is_shutdown_requested()
    
    request_shutdown()
    assert is_shutdown_requested()
    
    # Should still be in shutdown state
    assert shutdown_requested.is_set()


def test_threading_event_behavior():
    """Test the underlying threading.Event behavior."""
    # Reset state for clean test
    if shutdown_requested.is_set():
        shutdown_requested.clear()
    
    # Test wait behavior
    assert not shutdown_requested.wait(timeout=0.1)  # Should timeout
    
    # Set the event
    request_shutdown()
    
    # Now wait should return immediately
    assert shutdown_requested.wait(timeout=0.1)  # Should not timeout


def test_shutdown_state_persistence():
    """Test that shutdown state persists until explicitly cleared."""
    # Reset state for clean test
    if shutdown_requested.is_set():
        shutdown_requested.clear()
    
    # Request shutdown
    request_shutdown()
    assert is_shutdown_requested()
    
    # State should persist
    time.sleep(0.1)
    assert is_shutdown_requested()
    
    # Multiple checks should still return True
    for _ in range(10):
        assert is_shutdown_requested()


def test_concurrent_shutdown_checks():
    """Test concurrent shutdown state checks."""
    # Reset state for clean test
    if shutdown_requested.is_set():
        shutdown_requested.clear()
    
    check_results = []
    
    def check_shutdown():
        """Function to check shutdown state."""
        for _ in range(100):
            check_results.append(is_shutdown_requested())
            time.sleep(0.001)  # Small delay
    
    def trigger_shutdown():
        """Function to trigger shutdown after some checks."""
        time.sleep(0.05)  # Let some checks happen first
        request_shutdown()
    
    # Start checker thread
    checker_thread = threading.Thread(target=check_shutdown)
    trigger_thread = threading.Thread(target=trigger_shutdown)
    
    checker_thread.start()
    trigger_thread.start()
    
    # Wait for both to complete
    checker_thread.join()
    trigger_thread.join()
    
    # Analyze results
    assert len(check_results) == 100
    
    # Should have some False values at the beginning
    assert not all(check_results)  # Not all should be True
    assert any(check_results)      # Some should be True
    
    # The last values should all be True (after shutdown was triggered)
    assert check_results[-10:]  # Last 10 should all be True


def test_shutdown_integration_with_signal_handling():
    """Test shutdown integration simulating signal handling."""
    # Reset state for clean test
    if shutdown_requested.is_set():
        shutdown_requested.clear()
    
    # Simulate what happens in signal handler
    def simulate_signal_handler():
        """Simulate the signal handler behavior."""
        if is_shutdown_requested():
            # Second CTRL+C - force exit
            force_exit()
            return "force_exit"
        else:
            # First CTRL+C - graceful shutdown
            request_shutdown()
            return "graceful_shutdown"
    
    # First signal
    result1 = simulate_signal_handler()
    assert result1 == "graceful_shutdown"
    assert is_shutdown_requested()
    
    # Second signal (while shutdown is already requested)
    result2 = simulate_signal_handler()
    assert result2 == "force_exit"
    assert is_shutdown_requested()


def test_shutdown_state_module_level():
    """Test that the module-level shutdown_requested event works correctly."""
    # Reset state for clean test
    if shutdown_requested.is_set():
        shutdown_requested.clear()
    
    # Test direct access to module-level event
    assert not shutdown_requested.is_set()
    
    # Set via module function
    request_shutdown()
    assert shutdown_requested.is_set()
    
    # Check via module function
    assert is_shutdown_requested()
    
    # Clear manually for testing
    shutdown_requested.clear()
    assert not shutdown_requested.is_set()
    assert not is_shutdown_requested()


def test_shutdown_wait_functionality():
    """Test the wait functionality of the shutdown event."""
    # Reset state for clean test
    if shutdown_requested.is_set():
        shutdown_requested.clear()
    
    def delayed_shutdown():
        """Set shutdown after a delay."""
        time.sleep(0.2)
        request_shutdown()
    
    # Start the delayed shutdown
    shutdown_thread = threading.Thread(target=delayed_shutdown)
    start_time = time.time()
    shutdown_thread.start()
    
    # Wait for shutdown to be requested
    result = shutdown_requested.wait(timeout=1.0)
    end_time = time.time()
    
    # Clean up
    shutdown_thread.join()
    
    # Verify
    assert result  # Should have been set within timeout
    assert is_shutdown_requested()
    assert 0.15 < (end_time - start_time) < 0.3  # Should take about 0.2 seconds


def test_shutdown_timeout_behavior():
    """Test timeout behavior when shutdown is not requested."""
    # Reset state for clean test
    if shutdown_requested.is_set():
        shutdown_requested.clear()
    
    # Wait for shutdown with short timeout
    start_time = time.time()
    result = shutdown_requested.wait(timeout=0.1)
    end_time = time.time()
    
    # Verify
    assert not result  # Should have timed out
    assert not is_shutdown_requested()
    assert 0.08 < (end_time - start_time) < 0.15  # Should take about 0.1 seconds


def test_shutdown_state_reset():
    """Test that shutdown state can be reset for testing."""
    # Request shutdown
    request_shutdown()
    assert is_shutdown_requested()
    
    # Reset state (for testing purposes)
    shutdown_requested.clear()
    assert not is_shutdown_requested()
    
    # Can request shutdown again
    request_shutdown()
    assert is_shutdown_requested()


if __name__ == "__main__":
    pytest.main([__file__]) 