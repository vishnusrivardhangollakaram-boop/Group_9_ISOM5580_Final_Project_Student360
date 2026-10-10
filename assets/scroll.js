/* Trusted local enhancement. Never receives API keys, questions or report HTML. */
(() => {
  const config = () => document.querySelector('[data-s360-controller]');
  const enabled = () => config()?.dataset.s360Autoscroll === 'true';
  if (window.__student360Motion) {
    window.__student360Motion.schedule();
    return;
  }
  const state = { seen: new Set(), timer: null, lastManual: 0, pending: null };
  const reduced = () => window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const busyTyping = () => {
    const el = document.activeElement;
    return !!el && (el.matches('input:not([type=button]):not([type=submit]),textarea,[contenteditable=true]'));
  };
  const move = (target) => {
    target.scrollIntoView({ behavior: reduced() ? 'auto' : 'smooth', block: 'start' });
  };
  const update = () => {
    state.timer = null;
    const markers = [...document.querySelectorAll('[data-s360-scroll-key]')];
    const fresh = markers.filter(m => !state.seen.has(m.dataset.s360ScrollKey));
    const marker = fresh[fresh.length - 1];
    if (!marker) return;
    if (!enabled()) {
      fresh.forEach(m => state.seen.add(m.dataset.s360ScrollKey));
      return;
    }
    if (busyTyping() || Date.now() - state.lastManual < 1800) {
      state.timer = setTimeout(update, 1200);
      return;
    }
    // The latest rendered marker wins when a fast workflow goes straight to its report.
    fresh.forEach(m => state.seen.add(m.dataset.s360ScrollKey));
    move(marker);
    if (state.seen.size > 250) state.seen = new Set([...state.seen].slice(-150));
  };
  const schedule = () => {
    if (!state.timer) state.timer = setTimeout(update, 250);
  };
  document.addEventListener('wheel', () => { state.lastManual = Date.now(); }, { passive: true });
  document.addEventListener('touchmove', () => { state.lastManual = Date.now(); }, { passive: true });
  document.addEventListener('keydown', e => {
    if (['PageDown', 'PageUp', 'ArrowUp', 'ArrowDown', 'Home', 'End'].includes(e.key)) state.lastManual = Date.now();
  });
  document.addEventListener('focusout', schedule);
  document.addEventListener('click', e => {
    const trigger = e.target.closest('[data-s360-scroll-to]');
    if (!trigger) return;
    const target = document.getElementById(trigger.dataset.s360ScrollTo);
    if (target) { e.preventDefault(); move(target); }
  });
  const observer = new MutationObserver(schedule);
  observer.observe(document.body, { childList: true, subtree: true });
  window.__student360Motion = { schedule, observer };
  schedule();
})();
