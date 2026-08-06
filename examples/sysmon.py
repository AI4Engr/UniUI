"""
System Monitor - UniUI Demo  (btop-style)

Shows per-core CPU bars, memory bar, and top processes.
Same code runs on Qt and Jupyter — no platform checks.

Desktop:
    python sysmon.py              # auto-detect
    python sysmon.py --ui qt

Jupyter:
    from sysmon import create_sysmon_ui
    from uniui.display import show_ui
    show_ui(create_sysmon_ui("jupyter"), "System Monitor", 640, 580)
"""
import queue
import threading
import psutil
from uniui import use, VBox, HBox, Label, Button, TextArea, GroupBox, schedule_after
from uniui.display import show_ui, toggle_theme_and_refresh
from uniui.theme import is_dark

BAR_WIDTH = 20

_DARK  = {"green": "#4ade80", "yellow": "#facc15", "red": "#f87171",
           "dim": "#94a3b8", "fg": "#e2e8f0", "bg": "#1a1d2e"}
_LIGHT = {"green": "#16a34a", "yellow": "#d97706", "red": "#dc2626",
           "dim": "#6b7280",  "fg": "#1a1a2e",     "bg": "#ffffff"}

def _pal():
    return _DARK if is_dark() else _LIGHT


# ── HTML rendering ────────────────────────────────────────────────────────────

def _span(text, color):
    return f'<span style="color:{color}">{text}</span>'

def _pct_color(pct):
    p = _pal()
    return p["red"] if pct >= 80 else p["yellow"] if pct >= 50 else p["green"]

def _html_bar(pct, width=BAR_WIDTH):
    filled = max(0, min(width, int(round(pct / 100 * width))))
    return f'[{_span("█" * filled, _pct_color(pct))}{_span("░" * (width - filled), _pal()["dim"])}]'

def _render_cpu(stats):
    total = stats["cpu_total"]
    lines = [
        f"&nbsp;&nbsp;Total&nbsp;&nbsp;{_html_bar(total)} {_span(f'{total:5.1f}%', _pct_color(total))}",
        "",
    ]
    per  = stats["cpu_per"]
    half = (len(per) + 1) // 2
    for i in range(half):
        left  = f"&nbsp;&nbsp;Core{i:<2}&nbsp;{_html_bar(per[i], 12)} {_span(f'{per[i]:5.1f}%', _pct_color(per[i]))}"
        right = ""
        if i + half < len(per):
            j     = i + half
            right = f"&nbsp;&nbsp;Core{j:<2}&nbsp;{_html_bar(per[j], 12)} {_span(f'{per[j]:5.1f}%', _pct_color(per[j]))}"
        lines.append(f"{left}&nbsp;&nbsp;&nbsp;{right}")
    return "<br>".join(lines)

def _render_mem(stats):
    p = _pal()
    def row(label, pct, info):
        return (f"&nbsp;&nbsp;{label}&nbsp;&nbsp;{_html_bar(pct)} "
                f"{_span(f'{pct:5.1f}%', _pct_color(pct))}&nbsp;&nbsp;"
                f"{_span(info, p['dim'])}")
    return "<br>".join([
        row("RAM ", stats["mem_pct"], f"{stats['mem_used']:.1f} / {stats['mem_total']:.1f} GB"),
        row("Swap", stats["swap_pct"], f"{stats['swap_used']:.1f} GB used"),
    ])

def _render_procs(stats):
    p   = _pal()
    col = "{}&nbsp;&nbsp;{}&nbsp;&nbsp;{}&nbsp;&nbsp;{}&nbsp;&nbsp;{}"
    header = col.format(*[_span(h, p["dim"]) for h in ("   PID", " CPU%", " MEM%", "STA", "Name")])
    sep    = _span("─" * 52, p["dim"])
    lines  = [header, sep]
    for proc in stats["procs"]:
        lines.append(col.format(
            _span(f"{proc['pid']:>6}", p["fg"]),
            _span(f"{proc['cpu']:>5.1f}", _pct_color(proc["cpu"])),
            _span(f"{proc['mem']:>5.1f}", _pct_color(proc["mem"])),
            _span(f"{proc['status']:<3}", p["dim"]),
            _span(proc["name"], p["fg"]),
        ))
    return "<br>".join(lines)


# ── Data collection ───────────────────────────────────────────────────────────

def _collect():
    cpu_total = psutil.cpu_percent(interval=None)
    cpu_per   = psutil.cpu_percent(interval=None, percpu=True)
    mem       = psutil.virtual_memory()
    swap      = psutil.swap_memory()
    cpu_count = psutil.cpu_count() or 1
    procs = sorted(
        psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent", "status"]),
        key=lambda p: p.info["cpu_percent"] or 0,
        reverse=True,
    )[:12]
    return {
        "cpu_total": cpu_total,
        "cpu_per":   cpu_per or [],
        "mem_pct":   mem.percent,
        "mem_used":  mem.used  / 1024 ** 3,
        "mem_total": mem.total / 1024 ** 3,
        "swap_pct":  swap.percent,
        "swap_used": swap.used  / 1024 ** 3,
        "procs": [
            {
                "pid":    p.info["pid"],
                "name":   (p.info["name"] or "")[:18],
                "cpu":    min((p.info["cpu_percent"] or 0) / cpu_count, 99.9),
                "mem":    min(p.info["memory_percent"] or 0, 99.9),
                "status": (p.info["status"] or "")[:3],
            }
            for p in procs
        ],
    }


# ── UI ────────────────────────────────────────────────────────────────────────

def create_sysmon_ui(framework="auto"):
    use(framework)
    # Prime psutil cpu cache so first collect() returns real values immediately
    threading.Thread(target=lambda: psutil.cpu_percent(interval=0.5), daemon=True).start()

    cpu_area   = TextArea()
    mem_area   = TextArea()
    proc_area  = TextArea()
    status_lbl = Label("Stopped")
    toggle_btn = Button("▶  Start")
    theme_btn  = Button("☀  Light Mode")

    cpu_area.set_maximum_height(180)
    mem_area.set_maximum_height(70)
    proc_area.set_maximum_height(320)

    # Qt takes the monospace font from the stylesheet, Jupyter from set_html.

    layout = VBox(
        GroupBox("CPU",            layout=VBox(cpu_area)),
        GroupBox("Memory / Swap",  layout=VBox(mem_area)),
        GroupBox("Processes",      layout=VBox(proc_area)),
        HBox(toggle_btn, theme_btn, status_lbl),
    )

    running    = [False]
    last_stats = [None]
    data_queue = queue.Queue(maxsize=1)

    def _redraw(stats):
        cpu_area.set_html(_render_cpu(stats))
        mem_area.set_html(_render_mem(stats))
        proc_area.set_html(_render_procs(stats))

    def _poll():
        while not data_queue.empty():
            stats = data_queue.get_nowait()
            if "error" in stats:
                status_lbl.set_text(f"Error: {stats['error']}")
            else:
                last_stats[0] = stats
                _redraw(stats)
        if running[0]:
            schedule_after(500, _poll)

    def _collector():
        while running[0]:
            try:
                data_queue.put_nowait(_collect())
            except queue.Full:
                pass
            except Exception as e:
                try:
                    data_queue.put_nowait({"error": str(e)})
                except queue.Full:
                    pass
            threading.Event().wait(1.0)

    def on_toggle():
        if not running[0]:
            running[0] = True
            toggle_btn.set_text("■  Stop")
            status_lbl.set_text("Running  —  refresh ~1s")
            threading.Thread(target=_collector, daemon=True).start()
            schedule_after(100, _poll)
        else:
            running[0] = False
            toggle_btn.set_text("▶  Start")
            status_lbl.set_text("Stopped")

    def on_theme():
        now_dark = toggle_theme_and_refresh()
        theme_btn.set_text("☀  Light Mode" if now_dark else "🌙  Dark Mode")
        if last_stats[0] is not None:
            _redraw(last_stats[0])

    toggle_btn.connect(on_toggle)
    theme_btn.connect(on_theme)
    on_toggle()

    return layout


if __name__ == "__main__":
    from uniui import parse_args_ui
    show_ui(create_sysmon_ui(parse_args_ui()), "System Monitor", 640, 580)
