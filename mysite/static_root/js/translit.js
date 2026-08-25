/**
 * translit.js — Devanagari Transliteration
 * Usage: Add class="translit" to any input/textarea
 *        Add id="translitLang" to a <select> with values: en, hi, mr
 *
 * That's it. No wrappers. No extra HTML.
 */

(function () {
  // ── Inject CSS ─────────────────────────────────────────────────────────
  const style = document.createElement('style');
  style.textContent = `
    .translit-sug-box {
      position: absolute;
      top: 0; left: 0;
      background: #fff;
      border: 1px solid #ddd;
      border-radius: 6px;
      z-index: 99999;
      min-width: 180px;
      box-shadow: 0 4px 12px rgba(0,0,0,0.12);
      display: none;
      font-family: 'Noto Serif Devanagari', serif;
    }
    .translit-sug-box.open { display: block; }
    .translit-sug-item {
      padding: 8px 12px;
      cursor: pointer;
      font-size: 1rem;
      display: flex;
      justify-content: space-between;
      align-items: center;
      border-bottom: 1px solid #f0f0f0;
      color: #222;
    }
    .translit-sug-item:last-child { border-bottom: none; }
    .translit-sug-item:hover, .translit-sug-item.tl-active { background: #f5f0ff; }
    .translit-sug-item span { font-size: 0.68rem; color: #aaa; font-family: sans-serif; }
    .translit-sug-roman {
      border-top: 1px solid #eee;
      color: #888;
      font-family: sans-serif;
      font-size: 0.9rem;
      font-style: italic;
    }
  `;
  document.head.appendChild(style);

  // ── Single shared dropdown ─────────────────────────────────────────────
  const box = document.createElement('div');
  box.className = 'translit-sug-box';
  document.body.appendChild(box);

  // ── State ──────────────────────────────────────────────────────────────
  let lang = 'hi';
  let activeEl = null;
  let wordStart = 0;
  let currentWord = '';
  let sugs = [];
  let selIdx = -1;
  let timer = null;
  let justPicked = false;   // suppress re-fetch after a pick/click
  let pendingSpace = false; // space pressed while API call still in-flight

  // ── Language selector ──────────────────────────────────────────────────
  function bindLangSelect() {
    const sel = document.getElementById('language-select');
    if (!sel) return;
    lang = sel.value;
    sel.addEventListener('change', function () { lang = this.value; close(); });
  }

  // ── API ────────────────────────────────────────────────────────────────
  async function getSuggestions(word) {
    if (!word || lang === 'en') return [];
    try {
      const res = await fetch(
        `https://inputtools.google.com/request?itc=${lang}-t-i0-und&num=5&cp=0&cs=1&ie=utf-8&oe=utf-8&app=demopage&text=${encodeURIComponent(word)}`
      );
      const data = await res.json();
      return (data[0] === 'SUCCESS' && data[1]?.[0]?.[1]) ? data[1][0][1] : [];
    } catch { return []; }
  }

  // ── Word helpers ───────────────────────────────────────────────────────
  function getWord(el) {
    const v = el.value, c = el.selectionStart;
    let s = c - 1;
    while (s >= 0 && !/\s/.test(v[s])) s--;
    return { word: v.slice(s + 1, c), start: s + 1 };
  }

  function replaceWord(el, start, original, replacement) {
    el.value = el.value.slice(0, start) + replacement + el.value.slice(start + original.length);
    const pos = start + replacement.length;
    el.setSelectionRange(pos, pos);
    el.dispatchEvent(new Event('input',  { bubbles: true }));
    el.dispatchEvent(new Event('change', { bubbles: true }));
  }

  // Insert a literal space without triggering transliteration
  function insertSpace(el) {
    justPicked = true;
    const p = el.selectionStart;
    el.value = el.value.slice(0, p) + ' ' + el.value.slice(p);
    el.setSelectionRange(p + 1, p + 1);
    el.dispatchEvent(new Event('input', { bubbles: true }));
    setTimeout(() => { justPicked = false; }, 100);
  }

  // ── Position / rAF tracker ─────────────────────────────────────────────
  function positionBox(el) {
    const r = el.getBoundingClientRect();
    box.style.top      = (r.bottom + window.scrollY + 2) + 'px';
    box.style.left     = (r.left   + window.scrollX)     + 'px';
    box.style.minWidth = Math.max(r.width, 180)          + 'px';
  }

  let rafId = null;
  function startTracking() {
    if (rafId) return;
    (function frame() {
      if (!activeEl || !box.classList.contains('open')) { rafId = null; return; }
      positionBox(activeEl);
      rafId = requestAnimationFrame(frame);
    })();
  }
  function stopTracking() {
    if (rafId) { cancelAnimationFrame(rafId); rafId = null; }
  }

  // ── Show / close / pick ────────────────────────────────────────────────
  function show(el, items, roman) {
    // No suggestions returned
    if (!items.length) {
      if (pendingSpace) { pendingSpace = false; insertSpace(el); }
      close();
      return;
    }

    sugs = [...items, roman]; selIdx = -1;

    const rows = items.map((s, i) =>
      `<div class="translit-sug-item" data-i="${i}">${s}<span>${i + 1}</span></div>`
    );
    // Roman/English word as last option
    rows.push(`<div class="translit-sug-item translit-sug-roman" data-i="${items.length}">${roman}<span>en</span></div>`);

    box.innerHTML = rows.join('');
    box.querySelectorAll('.translit-sug-item').forEach(d =>
      d.addEventListener('mousedown', e => { e.preventDefault(); pick(+d.dataset.i); })
    );
    positionBox(el);
    box.classList.add('open');
    startTracking();

    // Space was pressed while this API call was still in-flight — auto-pick now
    if (pendingSpace) {
      pendingSpace = false;
      pick(0);
      insertSpace(el);
    }
  }

  function close() {
    box.classList.remove('open');
    stopTracking();
    sugs = []; selIdx = -1; activeEl = null;
    pendingSpace = false;
  }

  function pick(idx) {
    if (!activeEl || sugs[idx] === undefined) return;
    justPicked = true;
    const el = activeEl;
    replaceWord(el, wordStart, currentWord, sugs[idx]);
    close();
    el.focus();
    setTimeout(() => { justPicked = false; }, 100);
  }

  function highlight() {
    box.querySelectorAll('.translit-sug-item').forEach((el, i) =>
      el.classList.toggle('tl-active', i === selIdx)
    );
  }

  // ── Attach to one element ─────────────────────────────────────────────
  function attach(el) {
    el.addEventListener('input', function () {
      if (lang === 'en') { close(); return; }
      if (justPicked) return; // skip the input event fired by replaceWord / insertSpace
      clearTimeout(timer);
      const { word, start } = getWord(this);
      if (!word) { close(); return; }
      timer = setTimeout(async () => {
        const res = await getSuggestions(word);
        activeEl = el; currentWord = word; wordStart = start;
        show(el, res, word);
      }, 80);
    });

    el.addEventListener('keydown', function (e) {
      const isOpen = box.classList.contains('open') && activeEl === el;

      if (e.key === ' ') {
        if (isOpen && sugs.length) {
          // Suggestions visible -> pick first Devanagari, then insert space
          e.preventDefault();
          pick(0);
          insertSpace(this);
          return;
        }
        if (!isOpen && activeEl === el) {
          // API still in-flight -> hold the space, apply after suggestions arrive
          e.preventDefault();
          pendingSpace = true;
          return;
        }
      }

      if (e.key === 'ArrowDown' && isOpen) { e.preventDefault(); selIdx = Math.min(selIdx + 1, sugs.length - 1); highlight(); return; }
      if (e.key === 'ArrowUp'   && isOpen) { e.preventDefault(); selIdx = Math.max(selIdx - 1, 0); highlight(); return; }
      if ((e.key === 'Enter' || e.key === 'Tab') && isOpen && selIdx >= 0) { e.preventDefault(); pick(selIdx); return; }
      if (e.key === 'Escape' && isOpen) { e.preventDefault(); close(); return; }

      // Number shortcuts 1-5
      const n = parseInt(e.key);
      if (n >= 1 && n <= 5 && isOpen) { e.preventDefault(); pick(n - 1); }
    });

    el.addEventListener('blur', () => setTimeout(close, 150));
  }

  // ── Init ───────────────────────────────────────────────────────────────
  function init() {
    bindLangSelect();
    document.querySelectorAll('input.translit, textarea.translit').forEach(attach);

    // Handle dynamically added inputs
    new MutationObserver(mutations => {
      mutations.forEach(m => m.addedNodes.forEach(node => {
        if (node.nodeType !== 1) return;
        if (node.matches?.('input.translit, textarea.translit')) attach(node);
        node.querySelectorAll?.('input.translit, textarea.translit').forEach(attach);
      }));
    }).observe(document.body, { childList: true, subtree: true });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
