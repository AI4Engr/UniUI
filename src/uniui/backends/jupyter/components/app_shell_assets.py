"""Shell-specific markup and probes for the Jupyter Admin backend.

These are assets of the AppShell, not stylesheet rules: the splitter's drag
handler, the in-UI layout debug panel, and the standalone DOM measurement
snippet. They lived in ``styles.py`` only because that was where the shell's
CSS was.

Kept in their own module rather than inside ``app_shell.py`` so that importing
the AppShell adapter does not carry ~100 lines of embedded JavaScript, and so
the JS stays greppable as JS.
"""
from __future__ import annotations

from html import escape


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
