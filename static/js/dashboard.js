/* RGS TOWER — dashboard behaviour */
(function () {
  'use strict';
  const $  = (s, r) => (r || document).querySelector(s);
  const $$ = (s, r) => Array.from((r || document).querySelectorAll(s));

  /* dashboard is dark only — forget the old light/dark choice */
  try { localStorage.removeItem('rgs-theme'); } catch (e) {}

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

  /* several images → small previews */
  $$('[data-multi-preview]').forEach((input) => {
    input.addEventListener('change', () => {
      const box = input.parentElement && $('.multi-preview', input.parentElement);
      if (!box) return;
      box.innerHTML = '';
      Array.from(input.files || []).slice(0, 24).forEach((file) => {
        if (!file.type.startsWith('image/')) return;
        const img = document.createElement('img');
        img.src = URL.createObjectURL(file);
        box.appendChild(img);
      });
    });
  });

  /* work cover preview */
  const coverInput = $('#id_cover');
  if (coverInput) {
    coverInput.addEventListener('change', () => {
      const file = coverInput.files && coverInput.files[0];
      const target = $('[data-cover-preview]');
      if (!file || !target) return;
      const img = document.createElement('img');
      img.src = URL.createObjectURL(file);
      img.setAttribute('data-cover-preview', '');
      target.replaceWith(img);
    });
  }

  /* navbar link form: only show the field that matches the link type */
  const navForm = $('[data-nav-form]');
  if (navForm) {
    const type = $('#id_link_type', navForm);
    const show = (name, on) => {
      const field = $('[data-field="' + name + '"]', navForm);
      if (field) field.style.display = on ? '' : 'none';
    };
    const sync = () => {
      show('category', type.value === 'category');
      show('policy', type.value === 'policy');
      show('url', type.value === 'custom');
    };
    type.addEventListener('change', sync);
    sync();
  }

  /* select / clear every permission */
  $$('[data-check-all]').forEach((btn) => {
    btn.addEventListener('click', () => {
      const boxes = $$('input[type="checkbox"]', document.getElementById(btn.dataset.checkAll));
      const allOn = boxes.every((b) => b.checked);
      boxes.forEach((b) => { b.checked = !allOn; });
    });
  });
})();
