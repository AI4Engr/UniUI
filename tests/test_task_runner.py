"""
Unit tests for TaskRunner.

These tests run in-process with real threads. We patch schedule_after to
call the callback synchronously so tests don't depend on a Qt event loop.
"""
import threading
from unittest.mock import patch
from uniui.state import TaskRunner


def _run_sync(runner, fn, on_done=None, on_error=None, timeout=None, join_timeout=2.0):
    """Run fn on runner with schedule_after patched synchronous, then wait
    for the worker thread to finish before returning."""
    with patch("uniui.display.schedule_after", side_effect=lambda ms, cb: cb()):
        runner.run(fn, on_done=on_done, on_error=on_error, timeout=timeout)
        runner._thread.join(join_timeout)


def test_run_calls_on_done():
    runner = TaskRunner()
    result_holder = []

    def work(cancelled):
        return 42

    _run_sync(runner, work, on_done=result_holder.append)

    assert result_holder == [42]


def test_run_passes_cancelled_event():
    runner = TaskRunner()
    received_event = []

    def work(cancelled):
        received_event.append(cancelled)
        return "ok"

    _run_sync(runner, work, on_done=lambda r: None)

    assert received_event and isinstance(received_event[0], threading.Event)


def test_on_error_fires_on_exception():
    runner = TaskRunner()
    errors = []

    def work(cancelled):
        raise ValueError("boom")

    _run_sync(runner, work, on_error=errors.append)

    assert len(errors) == 1
    assert isinstance(errors[0], ValueError)
    assert str(errors[0]) == "boom"


def test_cancel_prevents_on_done():
    runner = TaskRunner()
    called = []
    started = threading.Event()

    def work(cancelled):
        started.set()
        cancelled.wait(timeout=2.0)
        return "result"

    with patch("uniui.display.schedule_after", side_effect=lambda ms, cb: cb()):
        runner.run(work, on_done=called.append)
        started.wait(timeout=1.0)
        runner.cancel()
        runner._thread.join(2.0)

    assert called == [], "on_done must not fire after cancel()"


def test_new_run_cancels_old():
    runner = TaskRunner()
    first_done_called = []
    second_result = []
    first_started = threading.Event()

    def work_first(cancelled):
        first_started.set()
        cancelled.wait(timeout=2.0)
        return "first"

    def work_second(cancelled):
        return "second"

    with patch("uniui.display.schedule_after", side_effect=lambda ms, cb: cb()):
        runner.run(work_first, on_done=first_done_called.append)
        first_started.wait(timeout=1.0)
        runner.run(work_second, on_done=second_result.append)
        runner._thread.join(2.0)

    assert second_result == ["second"]
    assert first_done_called == [], "first on_done must not fire after new run cancels it"


def test_run_without_callbacks_does_not_raise():
    runner = TaskRunner()
    done = threading.Event()

    def work(cancelled):
        done.set()
        return "ignored"

    _run_sync(runner, work)

    assert done.is_set(), "worker did not complete"


def test_timeout_fires_on_error_with_timeout_error():
    runner = TaskRunner()
    errors = []
    started = threading.Event()

    def work(cancelled):
        started.set()
        cancelled.wait(timeout=2.0)  # never finishes on its own
        return "too late"

    with patch("uniui.display.schedule_after", side_effect=lambda ms, cb: cb()):
        runner.run(work, on_error=errors.append, timeout=0.05)
        started.wait(timeout=1.0)
        runner._thread.join(2.0)

    assert len(errors) == 1
    assert isinstance(errors[0], TimeoutError)


def test_timeout_sets_the_cancelled_event():
    runner = TaskRunner()
    seen_cancelled = []
    started = threading.Event()

    def work(cancelled):
        started.set()
        cancelled.wait(timeout=2.0)
        seen_cancelled.append(cancelled.is_set())
        return "done"

    with patch("uniui.display.schedule_after", side_effect=lambda ms, cb: cb()):
        runner.run(work, timeout=0.05)
        started.wait(timeout=1.0)
        runner._thread.join(2.0)

    assert seen_cancelled == [True]


def test_fast_task_beats_its_own_timeout():
    """A task finishing before the timeout must call on_done, not on_error."""
    runner = TaskRunner()
    done_results = []
    errors = []

    def work(cancelled):
        return "fast"

    _run_sync(runner, work, on_done=done_results.append, on_error=errors.append, timeout=5.0)

    assert done_results == ["fast"]
    assert errors == []


def test_timeout_does_not_fire_after_normal_completion():
    """A short timeout that outlives the task must not call on_error late."""
    runner = TaskRunner()
    errors = []

    def work(cancelled):
        return "ok"

    _run_sync(runner, work, on_error=errors.append, timeout=0.2)

    assert errors == []


def test_no_timeout_means_task_can_run_indefinitely():
    runner = TaskRunner()
    errors = []

    def work(cancelled):
        return "ok"

    _run_sync(runner, work, on_error=errors.append)

    assert errors == []
