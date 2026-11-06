/**
 * Tiny DOM builder. Text is always added as text nodes (never innerHTML),
 * so question content can never inject markup.
 */
export function h(tag, props = {}, ...children) {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(props || {})) {
    if (v == null || v === false) continue;
    if (k === 'class') el.className = v;
    else if (k.startsWith('on') && typeof v === 'function') el.addEventListener(k.slice(2).toLowerCase(), v);
    else el.setAttribute(k, v === true ? '' : v);
  }
  for (const c of children.flat(Infinity)) {
    if (c == null || c === false) continue;
    el.append(c instanceof Node ? c : document.createTextNode(String(c)));
  }
  return el;
}

const SVG_NS = 'http://www.w3.org/2000/svg';

export function icon(pathData) {
  const svg = document.createElementNS(SVG_NS, 'svg');
  svg.setAttribute('viewBox', '0 0 24 24');
  svg.setAttribute('aria-hidden', 'true');
  svg.setAttribute('width', '24');
  svg.setAttribute('height', '24');
  const p = document.createElementNS(SVG_NS, 'path');
  p.setAttribute('d', pathData);
  p.setAttribute('fill', 'currentColor');
  svg.append(p);
  return svg;
}

/** Promise-based confirm built on <dialog>. Resolves true when confirmed. */
export function confirmDialog({ title, text, ok, cancel }) {
  return new Promise((resolve) => {
    const dlg = h('dialog', { class: 'dialog' },
      h('h2', {}, title),
      text ? h('p', {}, text) : null,
      h('div', { class: 'row end' },
        h('button', { class: 'btn text', onclick: () => dlg.close('no') }, cancel),
        h('button', { class: 'btn primary', onclick: () => dlg.close('yes') }, ok),
      ),
    );
    dlg.addEventListener('close', () => {
      dlg.remove();
      resolve(dlg.returnValue === 'yes');
    });
    document.body.append(dlg);
    dlg.showModal();
  });
}
