"""CSS, splitter markup and debug probes for the Jupyter Admin backend.

:func:`css` is an **f-string**. The web backend's equivalent block is a plain
string, so moving a rule between the two without adjusting the quoting emits a
literal ``{M['...']}`` into the stylesheet. ``tests/test_appearance_baseline.py``
guards both directions.

Every rule is scoped under ``.uniui-admin-shell``; the theme variables are
defined on that same selector, so moving variable emission out from under it is
what makes light mode render dark.
"""
from __future__ import annotations

from html import escape

from ...icons import ADMIN_ICON_NAMES, css_mask
from .runtime import M, get_palette


def shared_icon_css() -> str:
    rules = []
    for name in ADMIN_ICON_NAMES:
        rules.append(
            f".uniui-icon-{name} button::before{{content:'';display:inline-block;"
            f"width:18px;height:18px;flex:0 0 18px;margin-right:8px;"
            f"vertical-align:-4px;{css_mask(name)}}}"
        )
    return "".join(rules)


def css() -> str:
    p = get_palette()
    variables = ";".join(f"--uniui-{key}:{value}" for key, value in p.items())
    return f"""
<style>
{shared_icon_css()}
.uniui-admin-shell {{{variables};
  container-type:inline-size; width:100%; min-width:0; min-height:680px;
  color:var(--uniui-text); background:var(--uniui-bg);
  font-family:Inter,"Segoe UI Variable Text","Segoe UI",sans-serif;
  border:1px solid var(--uniui-border); border-radius:14px; overflow:hidden;
  box-shadow:var(--uniui-shadow); box-sizing:border-box;
}}
.uniui-admin-shell, .uniui-admin-shell * {{box-sizing:border-box}}
.uniui-admin-shell .widget-label {{color:var(--uniui-text)}}
.uniui-admin-shell .widget-text input {{
  color:var(--uniui-text)!important; background:var(--uniui-input_bg)!important;
  border:1px solid var(--uniui-border_strong)!important; border-radius:9px!important;
  min-height:38px; padding:7px 10px;
}}
.uniui-admin-shell .widget-button,
.uniui-admin-shell .widget-button button {{
  background:var(--uniui-accent)!important; color:white!important;
  border:1px solid var(--uniui-accent)!important; border-radius:9px!important;
  min-height:36px; padding:6px 13px; font-weight:600;
}}
.uniui-admin-shell .widget-button:hover,
.uniui-admin-shell .widget-button button:hover {{
  background:var(--uniui-accent_hover)!important;
  border-color:var(--uniui-accent_hover)!important;
}}
.uniui-admin-shell .widget-dropdown > select,
.uniui-admin-shell .widget-combobox input {{
  color:var(--uniui-text)!important; background:var(--uniui-input_bg)!important;
  border:1px solid var(--uniui-border_strong)!important; border-radius:9px!important;
  min-height:38px; padding:7px 30px 7px 10px; font-size:13px;
}}
.uniui-admin-shell .widget-dropdown > select:hover,
.uniui-admin-shell .widget-combobox input:hover {{border-color:var(--uniui-text_muted)!important}}
.uniui-admin-shell .widget-dropdown > select:focus,
.uniui-admin-shell .widget-combobox input:focus {{
  border:2px solid var(--uniui-accent)!important; outline:none;
}}
.uniui-admin-shell .widget-tab {{background:transparent; border:none}}
.uniui-admin-shell .widget-tab > .p-TabBar,
.uniui-admin-shell .widget-tab .lm-TabBar {{
  border-bottom:1px solid var(--uniui-border); overflow:visible;
}}
.uniui-admin-shell .widget-tab .p-TabBar-tab,
.uniui-admin-shell .widget-tab .lm-TabBar-tab {{
  background:transparent!important; border:none!important;
  color:var(--uniui-text_muted)!important; font-weight:600; font-size:13px;
  padding:9px 16px; min-height:0;
}}
.uniui-admin-shell .widget-tab .p-TabBar-tab.p-mod-current,
.uniui-admin-shell .widget-tab .lm-TabBar-tab.lm-mod-current {{
  color:var(--uniui-accent)!important;
  box-shadow:inset 0 -2px 0 var(--uniui-accent);
}}
.uniui-admin-shell .widget-tab .p-TabBar-tabLabel,
.uniui-admin-shell .widget-tab .lm-TabBar-tabLabel {{color:inherit}}
.uniui-admin-shell .widget-tab > .widget-tab-contents,
.uniui-admin-shell .widget-tab .p-StackedPanel,
.uniui-admin-shell .widget-tab .lm-StackedPanel {{
  border:none; background:transparent; padding:16px 2px 0;
}}
.uniui-demo-field {{gap:6px; min-width:190px}}
.uniui-demo-field-label, .uniui-demo-field-label .widget-label {{
  color:var(--uniui-text_muted)!important; font-size:12px; font-weight:650;
}}
.uniui-demo-swatch-row {{gap:10px; align-items:center; flex-wrap:wrap!important}}
.uniui-demo-swatch {{
  width:34px; height:34px; border-radius:9px; border:1px solid var(--uniui-border);
  flex:0 0 34px;
}}
.uniui-demo-badge-row {{gap:8px; flex-wrap:wrap!important}}
.uniui-shell-header {{
  flex:0 0 {M['header_height']}px; min-height:{M['header_height']}px; padding:0 16px; gap:10px;
  align-items:center; background:var(--uniui-header_bg);
  border-bottom:1px solid var(--uniui-border);
}}
.uniui-shell-body {{display:flex; width:100%; min-width:0; flex:1 1 auto}}
.uniui-shell-content {{
  min-width:0; flex:1 1 0; padding:{M['content_padding']}px {M['content_padding'] + 4}px {M['content_padding'] + 4}px;
  overflow:auto; background:var(--uniui-bg);
}}
.uniui-shell-footer {{
  flex:0 0 auto; min-height:{M['footer_height']}px; padding:8px 16px;
  background:var(--uniui-surface); border-top:1px solid var(--uniui-border);
}}
.uniui-admin-card {{
  width:100%; min-width:0; padding:{M['card_padding']}px {M['card_padding'] + 2}px; gap:{M['card_gap']}px;
  background:var(--uniui-surface); border:1px solid var(--uniui-border);
  border-radius:14px; box-shadow:none;
}}
.uniui-card-header {{display:flex; flex-flow:row; align-items:flex-start; gap:12px}}
.uniui-card-copy {{min-width:0; flex:1 1 auto; gap:2px}}
.uniui-card-title, .uniui-card-title p {{
  margin:0; color:var(--uniui-text); font-size:16px; font-weight:700;
}}
.uniui-card-subtitle, .uniui-card-subtitle p {{
  margin:0; color:var(--uniui-text_muted); font-size:12px;
}}
.uniui-stat-card {{
  min-width:190px; min-height:136px; padding:15px 18px 14px;
  background:var(--uniui-surface); border:1px solid var(--uniui-border);
  border-radius:14px;
  box-shadow:none; gap:1px; flex:1 1 190px;
}}
.uniui-stat-label, .uniui-stat-label p {{margin:0;color:var(--uniui-text_muted);font-size:{M['stat_label_size']}px;font-weight:600}}
.uniui-stat-value, .uniui-stat-value p {{margin:2px 0 0;color:var(--uniui-text);font-size:{M['stat_value_size']}px;line-height:1.15;font-weight:750}}
.uniui-stat-unit, .uniui-stat-unit p {{margin:0;color:var(--uniui-text_muted);font-size:11px}}
.uniui-stat-trend, .uniui-stat-trend p {{margin:9px 0 0;color:var(--uniui-text_muted);font-size:11px;font-weight:650}}
.uniui-stat-trend.uniui-up, .uniui-stat-trend.uniui-up p {{color:var(--uniui-ok)}}
.uniui-stat-trend.uniui-down, .uniui-stat-trend.uniui-down p {{color:var(--uniui-error)}}
.uniui-stat-trend.uniui-status-warn, .uniui-stat-trend.uniui-status-warn p {{color:var(--uniui-warn)}}
.uniui-stat-trend.uniui-status-error, .uniui-stat-trend.uniui-status-error p {{color:var(--uniui-error)}}
.uniui-metric-list-wrap {{width:100%; min-width:0}}
.uniui-metric-row {{display:flex; justify-content:space-between; align-items:center; padding:8px 0}}
.uniui-metric-row.uniui-metric-divider {{border-top:1px solid var(--uniui-border)}}
.uniui-metric-label {{color:var(--uniui-text_muted); font-size:{M['stat_label_size']}px}}
.uniui-metric-value {{color:var(--uniui-text); font-size:13px; font-weight:600}}
.uniui-admin-table {{width:100%; min-width:0}}
.uniui-admin-table table {{width:100%; border-collapse:separate; border-spacing:0; color:var(--uniui-text); font-size:13px}}
.uniui-admin-table th {{
  padding:10px 12px; text-align:left; color:var(--uniui-text_muted);
  background:var(--uniui-surface); border-bottom:1px solid var(--uniui-border);
  font-size:{M['stat_label_size']}px; font-weight:600;
}}
.uniui-admin-table td {{padding:11px 12px;border-bottom:1px solid var(--uniui-border)}}
.uniui-admin-table tbody tr {{cursor:pointer}}
.uniui-admin-table tbody tr:hover {{background:var(--uniui-surface_subtle)}}
.uniui-admin-table .uniui-number {{text-align:right}}
.uniui-status-pill {{display:inline-flex;align-items:center;min-height:24px;padding:3px 9px;
  border-radius:999px;font-size:11px;font-weight:700}}
.uniui-status-pill.uniui-status-ok {{color:var(--uniui-status_ok_fg);background:var(--uniui-status_ok_bg)}}
.uniui-status-pill.uniui-status-warn {{color:var(--uniui-status_warn_fg);background:var(--uniui-status_warn_bg)}}
.uniui-status-pill.uniui-status-error {{color:var(--uniui-status_error_fg);background:var(--uniui-status_error_bg)}}
.uniui-status-pill.uniui-status-neutral {{color:var(--uniui-status_neutral_fg);background:var(--uniui-status_neutral_bg)}}
.uniui-table-message, .uniui-table-message p {{margin:20px 0;text-align:center;color:var(--uniui-text_muted)}}
.uniui-admin-gauge,.uniui-admin-chart {{width:100%;min-width:0}}
.uniui-admin-gauge svg,.uniui-admin-chart svg {{display:block;width:100%;height:auto;max-height:250px}}
.uniui-admin-drawer {{max-height:0;opacity:0;overflow:hidden;transform:translateX(24px);
  pointer-events:none;padding:0 20px;background:var(--uniui-surface);border:1px solid transparent;
  border-radius:14px;transition:max-height .2s ease,opacity .18s ease,transform .2s ease,padding .2s ease}}
.uniui-admin-drawer.uniui-open {{max-height:520px;opacity:1;transform:none;pointer-events:auto;
  padding:18px 20px;border-color:var(--uniui-border);box-shadow:var(--uniui-shadow)}}
.uniui-drawer-header {{align-items:center}}
.uniui-drawer-title,.uniui-drawer-title p {{margin:0;color:var(--uniui-text);font-size:18px;font-weight:700}}
.uniui-admin-sidebar {{
  width:{M['sidebar_expanded']}px; min-width:{M['sidebar_min']}px;
  max-width:{M['sidebar_max']}px; flex:0 0 {M['sidebar_expanded']}px;
  padding:14px 10px; gap:5px; overflow:auto; background:var(--uniui-sidebar_bg);
}}
.uniui-admin-sidebar .widget-button {{width:100%}}
.uniui-admin-sidebar .widget-button,
.uniui-admin-sidebar .widget-button button {{
  width:100%; min-height:42px; padding:8px 11px; text-align:left;
  background:transparent!important; color:var(--uniui-sidebar_fg)!important;
  border-color:transparent!important; box-shadow:none!important;
}}
.uniui-admin-sidebar .widget-button:hover,
.uniui-admin-sidebar .widget-button button:hover,
.uniui-admin-sidebar .uniui-active,
.uniui-admin-sidebar .uniui-active button {{
  color:white!important; background:var(--uniui-sidebar_active)!important;
}}
.uniui-admin-sidebar .uniui-active {{box-shadow:inset {M['sidebar_edge_width']}px 0 0 var(--uniui-sidebar_edge)}}
.uniui-admin-sidebar .uniui-active button::before {{background:var(--uniui-accent)}}
.uniui-splitter-widget {{
  width:6px; min-width:6px; flex:0 0 6px; align-self:stretch;
  background:var(--uniui-border); cursor:col-resize; touch-action:none;
}}
.uniui-splitter-widget:hover, .uniui-splitter-widget:active {{background:var(--uniui-accent)}}
.uniui-splitter-handle {{width:100%;height:100%;min-height:520px;touch-action:none}}
.uniui-breadcrumb {{align-items:center;gap:4px;min-width:0}}
.uniui-breadcrumb .widget-button,
.uniui-breadcrumb .widget-button button {{
  min-height:28px;padding:2px 5px;background:transparent!important;
  color:var(--uniui-text_muted)!important;border-color:transparent!important;
}}
.uniui-breadcrumb-current, .uniui-breadcrumb-current p {{margin:0;color:var(--uniui-text);font-weight:650}}
.uniui-breadcrumb-separator, .uniui-breadcrumb-separator p {{margin:0;color:var(--uniui-text_muted)}}
.uniui-demo-page {{gap:{M['section_gap']}px;width:100%;min-width:0}}
.uniui-demo-heading {{gap:16px;align-items:center;flex-wrap:nowrap!important}}
.uniui-demo-subtitle .widget-label, .uniui-demo-subtitle {{color:var(--uniui-text)!important;font-size:17px;font-weight:650}}
.uniui-demo-hint .widget-label, .uniui-demo-hint {{color:var(--uniui-text_muted)!important}}
.uniui-demo-stats {{display:flex;flex-flow:row wrap;gap:{M['card_gap']}px;align-items:stretch}}
.uniui-demo-header-content {{width:100%;min-width:0;gap:8px;align-items:center;flex-wrap:nowrap!important}}
.uniui-demo-logo-mark, .uniui-demo-logo-mark .widget-label {{
  width:32px!important;min-width:32px;height:32px;display:grid;place-items:center;
  border-radius:9px;background:var(--uniui-accent);color:#fff!important;
  font-size:14px;font-weight:800;
}}
.uniui-demo-product, .uniui-demo-product .widget-label {{
  color:var(--uniui-text)!important;font-size:14px;font-weight:700;white-space:nowrap;
}}
.uniui-demo-avatar, .uniui-demo-avatar .widget-label {{
  width:32px!important;min-width:32px;height:32px;display:grid;place-items:center;
  border-radius:50%;background:var(--uniui-avatar_bg);color:var(--uniui-avatar_fg)!important;
  font-size:11px;font-weight:750;
}}
.uniui-admin-shell .uniui-demo-icon-button,
.uniui-admin-shell .uniui-demo-icon-button button {{
  width:32px!important;min-width:32px!important;height:32px;min-height:32px!important;
  padding:0!important;background:transparent!important;
  color:var(--uniui-text_muted)!important;border:1px solid transparent!important;
}}
.uniui-admin-shell .uniui-demo-icon-button button:hover {{
  background:var(--uniui-surface_subtle)!important;
  border-color:var(--uniui-border)!important;color:var(--uniui-text)!important;
}}
.uniui-admin-shell .uniui-demo-theme-button,
.uniui-admin-shell .uniui-demo-theme-button button {{
  min-height:34px!important;padding:0 12px!important;background:var(--uniui-surface)!important;
  color:var(--uniui-text)!important;border:1px solid var(--uniui-border_strong)!important;
}}
.uniui-admin-shell .uniui-demo-theme-button button:hover {{
  background:var(--uniui-surface_subtle)!important;
}}
.uniui-admin-shell .uniui-demo-primary-action,
.uniui-admin-shell .uniui-demo-primary-action button {{
  white-space:nowrap;background:var(--uniui-accent)!important;color:#fff!important;
  border-color:var(--uniui-accent)!important;
}}
.uniui-web-status-ok, .uniui-web-status-ok .widget-label {{
  color:var(--uniui-ok)!important;font-size:12px;font-weight:600;
}}
.uniui-web-footer-meta, .uniui-web-footer-meta .widget-label {{
  color:var(--uniui-text_muted)!important;font-size:12px;
}}
@container (max-width:1019px) {{
  .uniui-admin-sidebar {{width:{M['sidebar_collapsed']}px!important;min-width:{M['sidebar_collapsed']}px!important;max-width:{M['sidebar_collapsed']}px!important;flex-basis:{M['sidebar_collapsed']}px!important;padding:14px 8px}}
  .uniui-admin-sidebar .widget-button,
  .uniui-admin-sidebar .widget-button button {{font-size:0;text-align:center;padding:8px 4px}}
  .uniui-admin-sidebar .widget-button button::before {{margin-right:0}}
  .uniui-admin-sidebar .widget-button::first-letter,
  .uniui-admin-sidebar .widget-button button::first-letter {{font-size:16px}}
  .uniui-splitter-widget {{display:none!important}}
  .uniui-shell-content {{padding:22px 18px}}
}}
@container (max-width:719px) {{
  .uniui-shell-header {{padding:0 10px}}
  .uniui-shell-content {{padding:18px 12px}}
  .uniui-shell-footer {{display:none!important}}
}}
</style>
"""


SPLITTER_HTML = """
<div class="uniui-splitter-handle" title="Drag to resize navigation"
 onpointerdown="const h=this,root=h.closest('.uniui-shell-body'),side=root.querySelector('.uniui-admin-sidebar'),bridge=root.querySelector('.uniui-sidebar-width-bridge input'),sx=event.clientX,sw=side.getBoundingClientRect().width,pid=event.pointerId;h.setPointerCapture(pid);const move=e=>{const w=Math.max(168,Math.min(360,sw+e.clientX-sx));side.style.width=w+'px';side.style.minWidth=w+'px';side.style.maxWidth=w+'px';side.style.flex='0 0 '+w+'px';};const up=e=>{move(e);const w=Math.round(side.getBoundingClientRect().width);if(bridge){bridge.value=String(w);bridge.dispatchEvent(new Event('change',{bubbles:true}));}h.removeEventListener('pointermove',move);};h.addEventListener('pointermove',move);h.addEventListener('pointerup',up,{once:true});h.addEventListener('pointercancel',up,{once:true});">
</div>
"""


def debug_html(python_summary: str) -> str:
    """Build an in-UI layout probe that also measures the browser DOM."""
    return f"""
<div class="uniui-debug-panel" style="padding:10px 12px;background:#fff7ed;color:#7c2d12;
 border-bottom:1px solid #fdba74;font:12px/1.45 Consolas,monospace;white-space:normal">
  <div style="display:flex;align-items:center;gap:10px;margin-bottom:6px">
    <b>UniUI Jupyter layout debug</b>
    <button type="button" style="padding:3px 9px;border:1px solid #c2410c;border-radius:6px;
     background:#ffedd5;color:#7c2d12;cursor:pointer" onclick="
      const roots=document.querySelectorAll('.uniui-admin-shell');
      const root=this.closest('.uniui-admin-shell')||roots[roots.length-1];
      const out=this.parentElement.parentElement.querySelector('.uniui-debug-dom');
      const targets=[
        ['root',root],
        ['header',root&&root.querySelector('.uniui-shell-header')],
        ['body',root&&root.querySelector('.uniui-shell-body')],
        ['sidebar',root&&root.querySelector('.uniui-admin-sidebar')],
        ['content',root&&root.querySelector('.uniui-shell-content')],
        ['page',root&&root.querySelector('.uniui-demo-page')]
      ];
      out.textContent=targets.map(([name,el])=>{{
        if(!el)return name+': MISSING';
        const r=el.getBoundingClientRect(),s=getComputedStyle(el);
        el.style.outline='2px solid '+({{root:'#7c3aed',body:'#2563eb',content:'#dc2626',page:'#16a34a'}}[name]||'#f59e0b');
        return name+': rect='+Math.round(r.width)+'x'+Math.round(r.height)+
          ' @ '+Math.round(r.x)+','+Math.round(r.y)+
          ' display='+s.display+' visibility='+s.visibility+
          ' flex='+s.flex+' width='+s.width+' height='+s.height+
          ' overflow='+s.overflow+' children='+el.children.length;
      }}).join('\n');
    ">Measure DOM</button>
  </div>
  <pre style="margin:0 0 7px;white-space:pre-wrap">{escape(python_summary)}</pre>
  <pre class="uniui-debug-dom" style="margin:0;white-space:pre-wrap;color:#9a3412">
Click “Measure DOM”, then copy or screenshot these lines.</pre>
</div>
"""


DEBUG_MEASURE_JS = r"""
(() => {
  const roots = document.querySelectorAll('.uniui-admin-shell');
  const root = roots[roots.length - 1];
  document.querySelectorAll('.uniui-dom-debug-result').forEach(el => el.remove());
  if (!root) {
    const pre = document.createElement('pre');
    pre.className = 'uniui-dom-debug-result';
    pre.textContent = 'UniUI debug: .uniui-admin-shell was not found in the browser DOM';
    pre.style.cssText = 'padding:12px;background:#fee2e2;color:#991b1b;border:1px solid #ef4444';
    document.body.prepend(pre);
    return;
  }
  const targets = [
    ['root', root],
    ['header', root.querySelector('.uniui-shell-header')],
    ['body', root.querySelector('.uniui-shell-body')],
    ['sidebar', root.querySelector('.uniui-admin-sidebar')],
    ['content', root.querySelector('.uniui-shell-content')],
    ['page', root.querySelector('.uniui-demo-page')]
  ];
  const colors = {root:'#7c3aed', body:'#2563eb', content:'#dc2626', page:'#16a34a'};
  const lines = targets.map(([name, el]) => {
    if (!el) return name + ': MISSING';
    const r = el.getBoundingClientRect();
    const s = getComputedStyle(el);
    el.style.outline = '2px solid ' + (colors[name] || '#f59e0b');
    return name + ': rect=' + Math.round(r.width) + 'x' + Math.round(r.height) +
      ' @ ' + Math.round(r.x) + ',' + Math.round(r.y) +
      ' display=' + s.display + ' visibility=' + s.visibility +
      ' opacity=' + s.opacity + ' flex=' + s.flex +
      ' width=' + s.width + ' height=' + s.height +
      ' overflow=' + s.overflow + ' children=' + el.children.length;
  });
  const pre = document.createElement('pre');
  pre.className = 'uniui-dom-debug-result';
  pre.textContent = 'UniUI browser DOM measurements\n' + lines.join('\n');
  pre.style.cssText = 'margin:8px 0;padding:12px;white-space:pre-wrap;background:#fff7ed;color:#7c2d12;border:2px solid #f97316;border-radius:8px;font:12px/1.5 Consolas,monospace';
  root.insertAdjacentElement('beforebegin', pre);
})();
"""
