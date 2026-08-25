"""
Unit tests for TaskRunner.

These tests run in-process with real threads. We patch schedule_after to
call the callback synchronously so tests don't depend on a Qt event loop.
"""
import threading
import time
from unittest.mock import patch
from uniui.state import TaskRunner


def _sync_schedule(ms, cb):
    cb()


def _make_runner():
    """Create a TaskRunner with schedule_after patched to be synchronous."""
    return TaskRunner()


def _run_and_wait(runner, fn, on_done=None, on_error=None, timeout=2.0):
    """Run the task and wait for the worker thread to complete."""
    with patch("uniui.state.TaskRunner.run", wraps=runner.run):
        pass  # not needed with direct patch below

    done_event = threading.Event()
    orig_done = on_done
    orig_error = on_error

    thread_holder = [None]

    with patch("uniui.display.schedule_after", side_effect=lambda ms, cb: cb()):
        runner.run(fn, on_done=on_done, on_error=on_error)
        # Wait for the worker thread to finish
        t = runner._thread
        if t is not None:
            t.join(timeout)


def test_run_calls_on_done():
    runner = TaskRunner()
    result_holder = []
    done = threading.Event()

    def work(cancelled):
        return 42

    def on_done(r):
        result_holder.append(r)
        done.set()

    with patch("uniui.display.schedule_after", side_effect=lambda ms, cb: cb()):
        runner.run(work, on_done=on_done)
        runner._thread.join(timeout=2.0)

    assert result_holder == [42]


def test_run_passes_cancelled_event():
    runner = TaskRunner()
    received_event = []
    done = threading.Event()

    def work(cancelled):
        received_event.append(cancelled)
        return "ok"

    def on_done(r):
        done.set()

    with patch("uniui.display.schedule_after", side_effect=lambda ms, cb: cb()):
        runner.run(work, on_done=on_done)
        runner._thread.join(timeout=2.0)

    assert received_event and isinstance(received_event[0], threading.Event)


def test_on_error_fires_on_exception():
    runner = TaskRunner()
    errors = []

    def work(cancelled):
        raise ValueError("boom")

    def on_error(e):
        errors.append(e)

    with patch("uniui.display.schedule_after", side_effect=lambda ms, cb: cb()):
        runner.run(work, on_error=on_error)
        runner._thread.join(timeout=2.0)

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

    def on_done(r):
        called.append(r)

    with patch("uniui.display.schedule_after", side_effect=lambda ms, cb: cb()):
        runner.run(work, on_done=on_done)
        started.wait(timeout=1.0)
        runner.cancel()
        runner._thread.join(timeout=2.0)

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

    def on_done_first(r):
        first_done_called.append(r)

    def work_second(cancelled):
        return "second"

    def on_done_second(r):
        second_result.append(r)

    with patch("uniui.display.schedule_after", side_effect=lambda ms, cb: cb()):
        runner.run(work_first, on_done=on_done_first)
        first_started.wait(timeout=1.0)
        runner.run(work_second, on_done=on_done_second)
        runner._thread.join(timeout=2.0)

    assert second_result == ["second"]
    time.sleep(0.05)
    assert first_done_called == [], "first on_done must not fire after new run cancels it"


def test_run_without_callbacks_does_not_raise():
    runner = TaskRunner()
    done = threading.Event()

    def work(cancelled):
        done.set()
        return "ignored"

    with patch("uniui.display.schedule_after", side_effect=lambda ms, cb: cb()):
        runner.run(work)
        assert done.wait(timeout=2.0), "worker did not complete"


def test_timeout_fires_on_error_with_timeout_error():
    runner = TaskRunner()
    errors = []
    started = threading.Event()

    def work(cancelled):
        started.set()
        cancelled.wait(timeout=2.0)  # never finishes on its own
        return "too late"

    def on_error(e):
        errors.append(e)

    with patch("uniui.display.schedule_after", side_effect=lambda ms, cb: cb()):
        runner.run(work, on_error=on_error, timeout=0.05)
        started.wait(timeout=1.0)
        runner._thread.join(timeout=2.0)

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
        runner._thread.join(timeout=2.0)

    assert seen_cancelled == [True]


def test_fast_task_beats_its_own_timeout():
    """A task finishing before the timeout must call on_done, not on_error."""
    runner = TaskRunner()
    done_results = []
    errors = []

    def work(cancelled):
        return "fast"

    with patch("uniui.display.schedule_after", side_effect=lambda ms, cb: cb()):
        runner.run(work, on_done=done_results.append, on_error=errors.append, timeout=5.0)
        runner._thread.join(timeout=2.0)
        time.sleep(0.05)  # let a wrongly-armed timer prove it does nothing

    assert done_results == ["fast"]
    assert errors == []


def test_timeout_does_not_fire_after_normal_completion():
    """A short timeout that outlives the task must not call on_error late."""
    runner = TaskRunner()
    errors = []

    def work(cancelled):
        return "ok"

    with patch("uniui.display.schedule_after", side_effect=lambda ms, cb: cb()):
        runner.run(work, on_error=errors.append, timeout=0.2)
        runner._thread.join(timeout=2.0)
        time.sleep(0.3)  # past the timeout window

    assert errors == []


def test_no_timeout_means_task_can_run_indefinitely():
    runner = TaskRunner()
    errors = []
    started = threading.Event()

    def work(cancelled):
        started.set()
        return "ok" if cancelled.wait(timeout=0.2) else "ok"

    with patch("uniui.display.schedule_after", side_effect=lambda ms, cb: cb()):
        runner.run(work, on_error=errors.append)
        started.wait(timeout=1.0)
        runner._thread.join(timeout=2.0)

    assert errors == []
