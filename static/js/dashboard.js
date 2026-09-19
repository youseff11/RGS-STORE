/* RGS TOWER — dashboard behaviour */
(function () {
  'use strict';
  const $  = (s, r) => (r || document).querySelector(s);
  const $$ = (s, r) => Array.from((r || document).querySelectorAll(s));

  /* theme (shared key with the storefront) */
  const KEY = 'rgs-theme';
  function apply(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    $$('[data-theme-toggle]').forEach((btn) => {
      const sun = $('.ico-sun', btn), moon = $('.ico-moon', btn);
      if (sun && moon) {
        sun.style.display  = theme === 'dark' ? 'block' : 'none';
        moon.style.display = theme === 'dark' ? 'none' : 'block';
      }
    });
  }
  let current = 'dark';
  try {
    const stored = localStorage.getItem(KEY);
    current = (stored === 'light' || stored === 'dark') ? stored
      : (window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark');
  } catch (e) {}
  apply(current);

  /* mobile sidebar */
  const sidebar  = $('.sidebar');
  const backdrop = $('.sb-backdrop');
  const mobile   = window.matchMedia('(max-width: 900px)');
  const isOpen   = () => !!sidebar && sidebar.classList.contains('is-open');

  function setSidebar(open, returnFocus) {
    if (!sidebar) return;
    sidebar.classList.toggle('is-open', open);
    if (backdrop) backdrop.classList.toggle('is-open', open);
    document.body.classList.toggle('sb-locked', open);
    $$('[data-sb-toggle]').forEach((btn) => btn.setAttribute('aria-expanded', open ? 'true' : 'false'));
    if (open) {
      const closeBtn = $('.sb-close', sidebar);
      if (closeBtn) setTimeout(() => closeBtn.focus({ preventScroll: true }), 60);
    } else if (returnFocus) {
      const toggle = $('[data-sb-toggle]');
      if (toggle) toggle.focus({ preventScroll: true });
    }
  }

  document.addEventListener('click', (event) => {
    if (event.target.closest('[data-theme-toggle]')) {
      current = document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
      apply(current);
      try { localStorage.setItem(KEY, current); } catch (e) {}
    }
    if (event.target.closest('[data-sb-toggle]')) {
      setSidebar(!isOpen());
    } else if (event.target.closest('[data-sb-close]')) {
      setSidebar(false, true);
    } else if (mobile.matches && isOpen() && event.target.closest('.sidebar a')) {
      setSidebar(false);
    }
  });

  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && isOpen()) setSidebar(false, true);
  });

  const onViewport = () => { if (!mobile.matches && isOpen()) setSidebar(false); };
  if (mobile.addEventListener) mobile.addEventListener('change', onViewport);
  else if (mobile.addListener) mobile.addListener(onViewport);

  /* back/forward cache: never come back with the menu stuck open */
  window.addEventListener('pageshow', () => { if (isOpen()) setSidebar(false); });

  /* delete confirmations */
  document.addEventListener('submit', (event) => {
    const form = event.target;
    if (form.dataset.confirm && !window.confirm(form.dataset.confirm)) event.preventDefault();
  });

  /* toasts from server messages */
  function toast(message, kind) {
    let box = $('.toasts');
    if (!box) { box = document.createElement('div'); box.className = 'toasts'; document.body.appendChild(box); }
    const el = document.createElement('div');
    el.className = 'toast ' + (kind || 'info');
    el.innerHTML = '<span class="bar"></span><span></span>';
    el.lastElementChild.textContent = message;
    box.appendChild(el);
    setTimeout(() => el.remove(), 3600);
  }
  $$('[data-server-message]').forEach((el) => {
    toast(el.dataset.serverMessage, el.dataset.serverLevel || 'info');
    el.remove();
  });

  /* auto-slug preview + image preview */
  $$('input[type="file"]').forEach((input) => {
    input.addEventListener('change', () => {
      const target = input.closest('.field') && $('.file-preview', input.closest('.field'));
      if (!target || !input.files || !input.files[0]) return;
      const reader = new FileReader();
      reader.onload = (e) => { target.innerHTML = '<img src="' + e.target.result + '" style="max-height:120px;border-radius:10px;margin-top:8px">'; };
      reader.readAsDataURL(input.files[0]);
    });
  });

  /* stock matrix: fill a whole row / column quickly */
  $$('[data-fill-row]').forEach((btn) => {
    btn.addEventListener('click', () => {
      const value = window.prompt('الكمية لكل المقاسات في الصف ده؟', '10');
      if (value === null) return;
      $$('input', btn.closest('tr')).forEach((input) => { input.value = value; });
    });
  });

  /* scope toggle on the promotion form */
  const scope = $('#id_scope');
  if (scope) {
    const sync = () => {
      const catBlock = $('[data-scope="category"]');
      const proBlock = $('[data-scope="product"]');
      if (catBlock) catBlock.style.display = scope.value === 'category' ? '' : 'none';
      if (proBlock) proBlock.style.display = scope.value === 'product' ? '' : 'none';
    };
    scope.addEventListener('change', sync);
    sync();
  }
})();
