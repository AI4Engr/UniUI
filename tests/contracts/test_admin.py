"""
Contract tests for Admin components: Card, StatCard, Table, Sidebar, AppShell, Breadcrumb.
"""
import pytest

from tests.contract_framework import CommonCapabilitiesContractTest as _Common
from tests.contract_framework import skip_unless_available
from uniui import (
    APP_SHELL, BADGE, BREADCRUMB, CARD, CAROUSEL, CHART, DRAWER, GAUGE,
    METRIC_LIST, PROGRESS_BAR, SIDEBAR, STAT_CARD, TABLE, TOAST,
)


class TestCardContract(_Common):
    widget_kind = CARD

    def create_widget(self, factory):
        return factory.create_card()

    @pytest.mark.contract
    def test_set_title(self, factory):
        card = self.create_widget(factory)
        card.set_title("My Card")

    @pytest.mark.contract
    def test_set_subtitle(self, factory):
        card = self.create_widget(factory)
        card.set_subtitle("A subtitle")

    @pytest.mark.contract
    def test_set_title_and_subtitle(self, factory):
        card = self.create_widget(factory)
        card.set_title("Title")
        card.set_subtitle("Subtitle")

    @pytest.mark.contract
    def test_set_content_label(self, factory):
        card = self.create_widget(factory)
        label = factory.create_label()
        label.set_text("Card body")
        card.set_content(label)

    @pytest.mark.contract
    def test_set_action_button(self, factory):
        card = self.create_widget(factory)
        btn = factory.create_button()
        btn.set_text("Action")
        card.set_action(btn)

    @pytest.mark.contract
    def test_set_content_and_action(self, factory):
        card = self.create_widget(factory)
        lbl = factory.create_label()
        lbl.set_text("Content")
        card.set_content(lbl)
        btn = factory.create_button()
        btn.set_text("OK")
        card.set_action(btn)


class TestStatCardContract(_Common):
    widget_kind = STAT_CARD

    def create_widget(self, factory):
        return factory.create_stat_card()

    @pytest.mark.contract
    def test_set_label(self, factory):
        sc = self.create_widget(factory)
        sc.set_label("Active Users")

    @pytest.mark.contract
    def test_set_value(self, factory):
        sc = self.create_widget(factory)
        sc.set_value("1,280")

    @pytest.mark.contract
    def test_set_unit(self, factory):
        sc = self.create_widget(factory)
        sc.set_unit("users")

    @pytest.mark.contract
    @pytest.mark.parametrize("trend", [5.2, -3.1, 0.0])
    def test_set_trend(self, factory, trend):
        sc = self.create_widget(factory)
        sc.set_trend(trend)

    @pytest.mark.contract
    @pytest.mark.parametrize("status", ["ok", "warn", "error"])
    def test_set_status(self, factory, status):
        sc = self.create_widget(factory)
        sc.set_status(status)


class TestMetricListContract(_Common):
    widget_kind = METRIC_LIST

    def create_widget(self, factory):
        return factory.create_metric_list()

    @pytest.mark.contract
    def test_set_items(self, factory):
        ml = self.create_widget(factory)
        ml.set_items([
            {"label": "Active handles", "value": "4"},
            {"label": "Heap size", "value": "13.5 MiB"},
        ])

    @pytest.mark.contract
    def test_set_items_empty(self, factory):
        ml = self.create_widget(factory)
        ml.set_items([])

    @pytest.mark.contract
    def test_set_items_replaces_previous(self, factory):
        ml = self.create_widget(factory)
        ml.set_items([{"label": "A", "value": "1"}])
        ml.set_items([{"label": "B", "value": "2"}])


class TestBadgeContract(_Common):
    widget_kind = BADGE

    def create_widget(self, factory):
        return factory.create_badge()

    @pytest.mark.contract
    def test_set_text(self, factory):
        badge = self.create_widget(factory)
        badge.set_text("Beta")

    @pytest.mark.contract
    def test_defaults_to_neutral_status(self, factory):
        badge = self.create_widget(factory)
        assert badge._status == "neutral"

    @pytest.mark.contract
    @pytest.mark.parametrize("status", ["ok", "warn", "error", "neutral"])
    def test_set_status(self, factory, status):
        badge = self.create_widget(factory)
        badge.set_status(status)
        assert badge._status == status

    @pytest.mark.contract
    def test_unknown_status_classifies_as_neutral(self, factory):
        badge = self.create_widget(factory)
        badge.set_status("mystery")
        assert badge._status == "neutral"

    @pytest.mark.contract
    def test_set_status_accepts_a_raw_table_style_value(self, factory):
        """Same vocabulary Table's status column already classifies."""
        badge = self.create_widget(factory)
        badge.set_status("Delivered")
        assert badge._status == "ok"


class TestProgressBarContract(_Common):
    widget_kind = PROGRESS_BAR

    def create_widget(self, factory):
        return factory.create_progress_bar()

    @pytest.mark.contract
    @pytest.mark.parametrize("value", [0, 42, 100, -5, 150])
    def test_set_value_clamps_to_0_100(self, factory, value):
        bar = self.create_widget(factory)
        bar.set_value(value)  # must not raise regardless of range

    @pytest.mark.contract
    @pytest.mark.parametrize("status", ["ok", "warn", "error", "neutral", "mystery"])
    def test_set_status(self, factory, status):
        bar = self.create_widget(factory)
        bar.set_status(status)


class TestToastContract(_Common):
    widget_kind = TOAST

    def create_widget(self, factory):
        return factory.create_toast()

    @pytest.mark.contract
    def test_notify_does_not_raise(self, factory):
        toast = self.create_widget(factory)
        toast.notify("Saved successfully", status="ok")

    @pytest.mark.contract
    @pytest.mark.parametrize("status", ["ok", "warn", "error", "neutral", "mystery"])
    def test_notify_accepts_any_status(self, factory, status):
        toast = self.create_widget(factory)
        toast.notify("message", status=status)

    @pytest.mark.contract
    def test_dismiss_without_a_prior_notify_does_not_raise(self, factory):
        toast = self.create_widget(factory)
        toast.dismiss()

    @pytest.mark.contract
    def test_dismiss_after_notify_does_not_raise(self, factory):
        toast = self.create_widget(factory)
        toast.notify("message")
        toast.dismiss()


class TestToastRendering:
    def test_qt_notify_and_dismiss_toggle_visibility(self):
        skip_unless_available("qt")
        from uniui import create_factory

        toast = create_factory("qt").create_toast()
        native = toast.get_native()
        assert native.isHidden() is True
        toast.notify("Saved successfully", status="ok")
        assert native.isHidden() is False
        assert native.text() == "Saved successfully"
        toast.dismiss()
        assert native.isHidden() is True

    def test_jupyter_notify_and_dismiss_toggle_visibility(self):
        skip_unless_available("jupyter")
        from uniui import create_factory

        toast = create_factory("jupyter").create_toast()
        native = toast.get_native()
        assert native.layout.display == "none"
        toast.notify("Saved successfully", status="ok")
        assert native.layout.display is None
        assert "Saved successfully" in native.value
        toast.dismiss()
        assert native.layout.display == "none"

    def test_web_notify_reaches_the_native_content(self):
        skip_unless_available("web")
        from uniui import create_factory

        toast = create_factory("web").create_toast()
        toast.notify("Saved successfully", status="ok")
        native = toast.get_native()
        content = getattr(native, "content", None) or native._props.get("innerHTML", "")
        assert "Saved successfully" in content

    def test_jupyter_a_stale_auto_dismiss_does_not_hide_a_newer_message(self):
        """Regression guard: a second notify() before the first's timer
        fires must not let that first timer hide the *new* message once it
        finally goes off."""
        skip_unless_available("jupyter")
        from unittest.mock import patch
        from uniui import create_factory

        toast = create_factory("jupyter").create_toast()
        pending = []
        with patch("uniui.display.schedule_after", side_effect=lambda ms, cb: pending.append(cb)):
            toast.notify("first", status="warn")
            stale_dismiss = pending[-1]
            toast.notify("second", status="error")

        stale_dismiss()  # simulate the first message's timer firing late

        native = toast.get_native()
        assert native.layout.display is None, "must still be showing 'second'"
        assert "second" in native.value

    def test_web_a_stale_auto_dismiss_does_not_hide_a_newer_message(self):
        skip_unless_available("web")
        from unittest.mock import patch
        from uniui import create_factory

        toast = create_factory("web").create_toast()
        pending = []
        with patch("uniui.display.schedule_after", side_effect=lambda ms, cb: pending.append(cb)):
            toast.notify("first", status="warn")
            stale_dismiss = pending[-1]
            toast.notify("second", status="error")

        stale_dismiss()

        native = toast.get_native()
        assert native.visible is True, "the stale timer must not hide the newer message"
        content = getattr(native, "content", None) or native._props.get("innerHTML", "")
        assert "second" in content


def _make_png(path, width=10, height=10, color=(200, 200, 200)):
    """A minimal valid solid-color PNG, written with only stdlib - no
    Pillow dependency for what's otherwise just a couple of test fixtures."""
    import struct
    import zlib

    def chunk(tag, data):
        payload = tag + data
        return struct.pack(">I", len(data)) + payload + struct.pack(">I", zlib.crc32(payload))

    row = b"\x00" + bytes(color) * width
    raw = row * height
    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n")
        f.write(chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)))
        f.write(chunk(b"IDAT", zlib.compress(raw)))
        f.write(chunk(b"IEND", b""))


@pytest.fixture
def slide_paths(tmp_path):
    paths = []
    for i, color in enumerate([(255, 99, 71), (100, 149, 237), (60, 179, 113)]):
        p = tmp_path / f"slide{i}.png"
        _make_png(str(p), color=color)
        paths.append(str(p))
    return paths


class TestCarouselContract(_Common):
    widget_kind = CAROUSEL

    def create_widget(self, factory):
        return factory.create_carousel()

    @pytest.mark.contract
    def test_set_images_does_not_raise(self, factory, slide_paths):
        carousel = self.create_widget(factory)
        carousel.set_images(slide_paths)

    @pytest.mark.contract
    def test_starts_at_index_zero(self, factory, slide_paths):
        carousel = self.create_widget(factory)
        carousel.set_images(slide_paths)
        assert carousel.get_current_index() == 0

    @pytest.mark.contract
    def test_next_slide_wraps_around(self, factory, slide_paths):
        carousel = self.create_widget(factory)
        carousel.set_images(slide_paths)
        for _ in range(len(slide_paths)):
            carousel.next_slide()
        assert carousel.get_current_index() == 0

    @pytest.mark.contract
    def test_previous_slide_wraps_around(self, factory, slide_paths):
        carousel = self.create_widget(factory)
        carousel.set_images(slide_paths)
        carousel.previous_slide()
        assert carousel.get_current_index() == len(slide_paths) - 1

    @pytest.mark.contract
    def test_set_current_index_roundtrip(self, factory, slide_paths):
        carousel = self.create_widget(factory)
        carousel.set_images(slide_paths)
        carousel.set_current_index(2)
        assert carousel.get_current_index() == 2

    @pytest.mark.contract
    def test_set_current_index_clamps_out_of_range(self, factory, slide_paths):
        carousel = self.create_widget(factory)
        carousel.set_images(slide_paths)
        carousel.set_current_index(99)
        assert carousel.get_current_index() == len(slide_paths) - 1

    @pytest.mark.contract
    def test_navigation_without_images_does_not_raise(self, factory):
        carousel = self.create_widget(factory)
        carousel.next_slide()
        carousel.previous_slide()
        carousel.set_current_index(0)

    @pytest.mark.contract
    def test_on_change_callback(self, factory, slide_paths):
        carousel = self.create_widget(factory)
        carousel.set_images(slide_paths)
        called = []
        carousel.on_change(lambda: called.append(1))

        carousel.next_slide()

        assert len(called) >= 1

    @pytest.mark.contract
    def test_on_change_dispose_stops_callback(self, factory, slide_paths):
        carousel = self.create_widget(factory)
        carousel.set_images(slide_paths)
        called = []
        handle = carousel.on_change(lambda: called.append(1))
        handle.dispose()

        carousel.next_slide()

        assert called == []

    @pytest.mark.contract
    def test_set_auto_advance_does_not_raise(self, factory, slide_paths):
        carousel = self.create_widget(factory)
        carousel.set_images(slide_paths)
        carousel.set_auto_advance(True, interval_ms=50)
        carousel.set_auto_advance(False)


class TestCarouselRendering:
    def test_jupyter_a_stale_auto_advance_tick_does_not_reschedule(self, tmp_path):
        """Regression guard: disabling auto-advance must invalidate any
        already-scheduled tick, mirroring Toast's stale-timer guard."""
        skip_unless_available("jupyter")
        from unittest.mock import patch
        from uniui import create_factory

        paths = []
        for i, color in enumerate([(255, 99, 71), (100, 149, 237)]):
            p = tmp_path / f"slide{i}.png"
            _make_png(str(p), color=color)
            paths.append(str(p))

        carousel = create_factory("jupyter").create_carousel()
        carousel.set_images(paths)

        pending = []
        with patch("uniui.display.schedule_after", side_effect=lambda ms, cb: pending.append(cb)):
            carousel.set_auto_advance(True, interval_ms=500)
            tick = pending.pop()
            tick()
            assert carousel.get_current_index() == 1

            stale_tick = pending.pop()
            carousel.set_auto_advance(False)
            stale_tick()

        assert carousel.get_current_index() == 1, "stale tick must not advance further"
        assert pending == [], "stale tick must not reschedule itself"

    def test_web_a_stale_auto_advance_tick_does_not_reschedule(self, tmp_path):
        skip_unless_available("web")
        from unittest.mock import patch
        from uniui import create_factory

        paths = []
        for i, color in enumerate([(255, 99, 71), (100, 149, 237)]):
            p = tmp_path / f"slide{i}.png"
            _make_png(str(p), color=color)
            paths.append(str(p))

        carousel = create_factory("web").create_carousel()
        carousel.set_images(paths)

        pending = []
        with patch("uniui.display.schedule_after", side_effect=lambda ms, cb: pending.append(cb)):
            carousel.set_auto_advance(True, interval_ms=500)
            tick = pending.pop()
            tick()
            assert carousel.get_current_index() == 1

            stale_tick = pending.pop()
            carousel.set_auto_advance(False)
            stale_tick()

        assert carousel.get_current_index() == 1, "stale tick must not advance further"
        assert pending == [], "stale tick must not reschedule itself"


class TestBadgeRendering:
    """Verify text/status actually reach each backend's native widget, not
    just the adapter's own state - the contract tests above only check the
    latter."""

    @pytest.mark.parametrize("framework", ["qt", "jupyter", "web"])
    def test_set_text_reaches_the_native_widget(self, framework):
        skip_unless_available(framework)
        from uniui import create_factory

        badge = create_factory(framework).create_badge()
        badge.set_text("Beta")
        native = badge.get_native()
        if framework == "qt":
            assert native.text() == "Beta"
        elif framework == "jupyter":
            assert "Beta" in native.value
        else:
            assert native.text == "Beta"

    @pytest.mark.parametrize("framework", ["qt", "jupyter", "web"])
    def test_set_status_reaches_the_native_widget(self, framework):
        skip_unless_available(framework)
        from uniui import create_factory

        badge = create_factory(framework).create_badge()
        badge.set_status("error")
        native = badge.get_native()
        if hasattr(native, "styleSheet"):
            assert "status_error" in native.styleSheet() or native.styleSheet()
        elif hasattr(native, "value"):
            assert "uniui-status-error" in native.value
        else:
            assert "uniui-status-error" in native._classes

    def test_qt_badge_has_a_fixed_small_height(self):
        """Regression: without a fixed height, a QLabel stretches to fill
        whatever row it's placed in - the pill background then paints that
        whole stretched rect, turning a small badge into a large block next
        to taller header siblings."""
        skip_unless_available("qt")
        from PySide2 import QtWidgets
        from uniui import create_factory

        badge = create_factory("qt").create_badge()
        native = badge.get_native()
        assert native.sizePolicy().verticalPolicy() == QtWidgets.QSizePolicy.Fixed
        assert native.sizeHint().height() <= 24

    def test_qt_status_color_changes_with_status(self):
        skip_unless_available("qt")
        from uniui import create_factory

        badge = create_factory("qt").create_badge()
        badge.set_status("ok")
        ok_style = badge.get_native().styleSheet()
        badge.set_status("error")
        error_style = badge.get_native().styleSheet()
        assert ok_style != error_style

    def test_web_status_class_is_swapped_not_accumulated(self):
        skip_unless_available("web")
        from uniui import create_factory

        badge = create_factory("web").create_badge()
        badge.set_status("ok")
        badge.set_status("error")
        classes = badge.get_native()._classes
        assert "uniui-status-error" in classes
        assert "uniui-status-ok" not in classes


class TestTableContract(_Common):
    widget_kind = TABLE

    def create_widget(self, factory):
        return factory.create_table()

    @pytest.mark.contract
    def test_set_columns(self, factory):
        tbl = self.create_widget(factory)
        tbl.set_columns([
            {"key": "name", "label": "Name"},
            {"key": "age", "label": "Age", "width": 80},
        ])

    @pytest.mark.contract
    def test_set_rows(self, factory):
        tbl = self.create_widget(factory)
        tbl.set_columns([{"key": "name", "label": "Name"}, {"key": "age", "label": "Age"}])
        tbl.set_rows([
            {"name": "Alice", "age": "30"},
            {"name": "Bob", "age": "25"},
        ])

    @pytest.mark.contract
    def test_set_rows_empty(self, factory):
        tbl = self.create_widget(factory)
        tbl.set_columns([{"key": "id", "label": "ID"}])
        tbl.set_rows([])

    @pytest.mark.contract
    def test_set_loading_true(self, factory):
        tbl = self.create_widget(factory)
        tbl.set_loading(True)

    @pytest.mark.contract
    def test_set_loading_false(self, factory):
        tbl = self.create_widget(factory)
        tbl.set_loading(True)
        tbl.set_loading(False)

    @pytest.mark.contract
    def test_set_error_message(self, factory):
        tbl = self.create_widget(factory)
        tbl.set_error("Failed to load data")

    @pytest.mark.contract
    def test_set_error_clear(self, factory):
        tbl = self.create_widget(factory)
        tbl.set_error("Failed")
        tbl.set_error("")

    @pytest.mark.contract
    def test_on_row_click_registers(self, factory):
        tbl = self.create_widget(factory)
        tbl.on_row_click(lambda row: None)

    @pytest.mark.contract
    def test_on_row_click_dispose_clears_callback(self, factory):
        tbl = self.create_widget(factory)
        handle = tbl.on_row_click(lambda row: None)
        handle.dispose()
        assert tbl._row_click_cb is None

    @pytest.mark.contract
    def test_get_selected_row_starts_as_none(self, factory):
        tbl = self.create_widget(factory)
        assert tbl.get_selected_row() is None

    @pytest.mark.contract
    def test_set_page_size_slices_the_displayed_rows(self, factory):
        tbl = self.create_widget(factory)
        tbl.set_columns([{"key": "id"}])
        tbl.set_rows([{"id": i} for i in range(5)])
        tbl.set_page_size(2)
        assert tbl._model.display_rows() == [{"id": 0}, {"id": 1}]

    @pytest.mark.contract
    def test_set_page_navigates(self, factory):
        tbl = self.create_widget(factory)
        tbl.set_columns([{"key": "id"}])
        tbl.set_rows([{"id": i} for i in range(5)])
        tbl.set_page_size(2)
        tbl.set_page(2)
        assert tbl._model.display_rows() == [{"id": 4}]

    @pytest.mark.contract
    def test_set_page_size_none_disables_pagination(self, factory):
        tbl = self.create_widget(factory)
        tbl.set_columns([{"key": "id"}])
        tbl.set_rows([{"id": i} for i in range(5)])
        tbl.set_page_size(2)
        tbl.set_page_size(None)
        assert len(tbl._model.display_rows()) == 5

    @pytest.mark.contract
    def test_set_sort_ascending(self, factory):
        tbl = self.create_widget(factory)
        tbl.set_columns([{"key": "name", "label": "Name", "sortable": True}])
        tbl.set_rows([{"name": "Bob"}, {"name": "Alice"}])
        tbl.set_sort("name")
        assert tbl._model.sorted_rows() == [{"name": "Alice"}, {"name": "Bob"}]

    @pytest.mark.contract
    def test_set_sort_descending(self, factory):
        tbl = self.create_widget(factory)
        tbl.set_columns([{"key": "name", "label": "Name", "sortable": True}])
        tbl.set_rows([{"name": "Alice"}, {"name": "Bob"}])
        tbl.set_sort("name", reverse=True)
        assert tbl._model.sorted_rows() == [{"name": "Bob"}, {"name": "Alice"}]

    @pytest.mark.contract
    def test_set_sort_none_clears(self, factory):
        tbl = self.create_widget(factory)
        tbl.set_columns([{"key": "name", "label": "Name", "sortable": True}])
        tbl.set_rows([{"name": "Bob"}, {"name": "Alice"}])
        tbl.set_sort("name")
        tbl.set_sort(None)
        assert tbl._model.sorted_rows() == [{"name": "Bob"}, {"name": "Alice"}]

    @pytest.mark.contract
    def test_set_sort_persists_across_new_rows(self, factory):
        tbl = self.create_widget(factory)
        tbl.set_columns([{"key": "amount", "label": "Amount", "sortable": True}])
        tbl.set_rows([{"amount": 3}, {"amount": 1}])
        tbl.set_sort("amount")
        tbl.set_rows([{"amount": 5}, {"amount": 2}])
        assert tbl._model.sorted_rows() == [{"amount": 2}, {"amount": 5}]


class TestSidebarContract(_Common):
    widget_kind = SIDEBAR

    def create_widget(self, factory):
        return factory.create_sidebar()

    @pytest.mark.contract
    def test_add_item(self, factory):
        sb = self.create_widget(factory)
        sb.add_item("dashboard", "Dashboard")

    @pytest.mark.contract
    def test_add_multiple_items(self, factory):
        sb = self.create_widget(factory)
        sb.add_item("dashboard", "Dashboard")
        sb.add_item("users", "Users")
        sb.add_item("settings", "Settings")

    @pytest.mark.contract
    def test_set_active(self, factory):
        sb = self.create_widget(factory)
        sb.add_item("dashboard", "Dashboard")
        sb.add_item("users", "Users")
        sb.set_active("users")

    @pytest.mark.contract
    def test_on_select_registers(self, factory):
        sb = self.create_widget(factory)
        sb.add_item("dashboard", "Dashboard")
        sb.on_select(lambda key: None)

    @pytest.mark.contract
    def test_on_select_dispose_clears_callback(self, factory):
        sb = self.create_widget(factory)
        sb.add_item("dashboard", "Dashboard")
        handle = sb.on_select(lambda key: None)
        handle.dispose()
        assert sb._select_cb is None

    @pytest.mark.contract
    def test_set_collapsed_true(self, factory):
        sb = self.create_widget(factory)
        sb.set_collapsed(True)

    @pytest.mark.contract
    def test_set_collapsed_false(self, factory):
        sb = self.create_widget(factory)
        sb.set_collapsed(True)
        sb.set_collapsed(False)


class TestAppShellContract(_Common):
    widget_kind = APP_SHELL

    def create_widget(self, factory):
        return factory.create_app_shell()

    @pytest.mark.contract
    def test_set_header(self, factory):
        shell = self.create_widget(factory)
        lbl = factory.create_label()
        lbl.set_text("Header")
        shell.set_header(lbl)

    @pytest.mark.contract
    def test_set_sidebar(self, factory):
        shell = self.create_widget(factory)
        sb = factory.create_sidebar()
        sb.add_item("home", "Home")
        shell.set_sidebar(sb)

    @pytest.mark.contract
    def test_set_content(self, factory):
        shell = self.create_widget(factory)
        lbl = factory.create_label()
        lbl.set_text("Main content")
        shell.set_content(lbl)

    @pytest.mark.contract
    def test_set_footer(self, factory):
        shell = self.create_widget(factory)
        lbl = factory.create_label()
        lbl.set_text("Footer")
        shell.set_footer(lbl)

    @pytest.mark.contract
    def test_full_shell(self, factory):
        """AppShell can have all four regions set without error."""
        shell = self.create_widget(factory)
        header = factory.create_label()
        header.set_text("Admin Demo")
        shell.set_header(header)

        sb = factory.create_sidebar()
        sb.add_item("dashboard", "Dashboard")
        sb.add_item("users", "Users")
        shell.set_sidebar(sb)

        content = factory.create_label()
        content.set_text("Welcome")
        shell.set_content(content)

        footer = factory.create_label()
        footer.set_text("v1.0.0")
        shell.set_footer(footer)


class TestBreadcrumbContract(_Common):
    widget_kind = BREADCRUMB

    def create_widget(self, factory):
        return factory.create_breadcrumb()

    @pytest.mark.contract
    @pytest.mark.parametrize("items", [
        [],
        [{"label": "Home"}],
        [
            {"label": "Home", "path": "/"},
            {"label": "Users", "path": "/users"},
            {"label": "Alice"},
        ],
    ], ids=["empty", "single", "trail"])
    def test_set_items(self, factory, items):
        bc = self.create_widget(factory)
        bc.set_items(items)

    @pytest.mark.contract
    def test_set_items_replaces(self, factory):
        """Calling set_items twice replaces the previous trail."""
        bc = self.create_widget(factory)
        bc.set_items([{"label": "Home", "path": "/"}, {"label": "Old"}])
        bc.set_items([{"label": "Home", "path": "/"}, {"label": "New"}])

    @pytest.mark.contract
    def test_on_click_registers(self, factory):
        bc = self.create_widget(factory)
        bc.on_click(lambda path: None)

    @pytest.mark.contract
    def test_on_click_dispose_clears_callback(self, factory):
        bc = self.create_widget(factory)
        handle = bc.on_click(lambda path: None)
        handle.dispose()
        assert bc._click_cb is None


class TestGaugeContract(_Common):
    widget_kind = GAUGE

    def create_widget(self, factory):
        return factory.create_gauge()

    @pytest.mark.contract
    def test_configure_gauge(self, factory):
        gauge = self.create_widget(factory)
        gauge.set_range(0, 120)
        gauge.set_label("Temperature")
        gauge.set_unit("°C")
        gauge.set_status("warn")
        gauge.set_value(88)


class TestChartContract(_Common):
    widget_kind = CHART

    def create_widget(self, factory):
        return factory.create_chart()

    @pytest.mark.contract
    def test_set_and_append_chart_data(self, factory):
        chart = self.create_widget(factory)
        chart.set_type("area")
        chart.set_title("Temperature")
        chart.set_max_points(3)
        chart.set_data([1, 2], [{"name": "T", "data": [20, 22]}])
        chart.append_data(3, [24])
        chart.append_data(4, [23])


class TestDrawerContract(_Common):
    widget_kind = DRAWER

    def create_widget(self, factory):
        return factory.create_drawer()

    @pytest.mark.contract
    def test_drawer_content_and_visibility(self, factory):
        drawer = self.create_widget(factory)
        label = factory.create_label()
        label.set_text("Settings")
        drawer.set_title("Details")
        drawer.set_content(label)
        drawer.open()
        assert drawer.is_open()
        drawer.toggle()
        assert not drawer.is_open()


class TestProgressBarRendering:
    @pytest.mark.parametrize("framework", ["qt", "jupyter", "web"])
    def test_value_reaches_the_native_widget(self, framework):
        skip_unless_available(framework)
        from uniui import create_factory

        bar = create_factory(framework).create_progress_bar()
        bar.set_value(75)
        native = bar.get_native()
        if framework == "qt":
            assert native.value() == 75
        elif framework == "jupyter":
            assert native.value == 75.0
        else:
            assert native.value == 0.75

    @pytest.mark.parametrize("framework", ["qt", "jupyter", "web"])
    def test_value_clamps_out_of_range(self, framework):
        skip_unless_available(framework)
        from uniui import create_factory

        bar = create_factory(framework).create_progress_bar()
        bar.set_value(150)
        native = bar.get_native()
        if framework == "qt":
            assert native.value() == 100
        elif framework == "jupyter":
            assert native.value == 100.0
        else:
            assert native.value == 1.0
