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

  document.addEventListener('click', (event) => {
    if (event.target.closest('[data-theme-toggle]')) {
      current = document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
      apply(current);
      try { localStorage.setItem(KEY, current); } catch (e) {}
    }
    if (event.target.closest('[data-sb-toggle]')) {
      const sb = $('.sidebar');
      sb && sb.classList.toggle('is-open');
    }
  });

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
