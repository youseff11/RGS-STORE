/* RGS TOWER — storefront behaviour */
(function () {
  'use strict';

  const $  = (sel, root) => (root || document).querySelector(sel);
  const $$ = (sel, root) => Array.from((root || document).querySelectorAll(sel));

  /* ------------------------------------------------------------ theme ---- */
  const THEME_KEY = 'rgs-theme';

  function readTheme() {
    try {
      const stored = localStorage.getItem(THEME_KEY);
      if (stored === 'light' || stored === 'dark') return stored;
    } catch (e) { /* storage unavailable */ }
    return window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark';
  }

  function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    $$('[data-theme-toggle]').forEach((btn) => {
      btn.setAttribute('aria-label', theme === 'dark' ? 'Light mode' : 'Dark mode');
      const sun = $('.ico-sun', btn);
      const moon = $('.ico-moon', btn);
      if (sun && moon) {
        sun.style.display  = theme === 'dark' ? 'block' : 'none';
        moon.style.display = theme === 'dark' ? 'none' : 'block';
      }
    });
  }

  applyTheme(readTheme());

  document.addEventListener('click', (event) => {
    const toggle = event.target.closest('[data-theme-toggle]');
    if (!toggle) return;
    const next = document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
    applyTheme(next);
    try { localStorage.setItem(THEME_KEY, next); } catch (e) { /* ignore */ }
  });

  /* ------------------------------------------------------------ toasts --- */
  function toast(message, kind) {
    let box = $('.toasts');
    if (!box) {
      box = document.createElement('div');
      box.className = 'toasts';
      document.body.appendChild(box);
    }
    const el = document.createElement('div');
    el.className = 'toast ' + (kind || 'info');
    el.innerHTML = '<span class="bar"></span><span></span>';
    el.lastElementChild.textContent = message;
    box.appendChild(el);
    setTimeout(() => {
      el.classList.add('out');
      setTimeout(() => el.remove(), 320);
    }, 3200);
  }
  window.rgsToast = toast;

  /* ------------------------------------------------------------ header --- */
  const header = $('.header');
  if (header) {
    const onScroll = () => header.classList.toggle('is-stuck', window.scrollY > 8);
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
  }

  const drawer = $('.drawer');
  document.addEventListener('click', (event) => {
    if (event.target.closest('[data-drawer-open]')) {
      drawer && drawer.classList.add('is-open');
      document.body.style.overflow = 'hidden';
    }
    if (event.target.closest('[data-drawer-close]') || event.target.classList.contains('drawer-veil')) {
      drawer && drawer.classList.remove('is-open');
      document.body.style.overflow = '';
    }
    if (event.target.closest('[data-filters-toggle]')) {
      const panel = $('.filters');
      panel && panel.classList.toggle('is-open');
    }
  });

  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && drawer && drawer.classList.contains('is-open')) {
      drawer.classList.remove('is-open');
      document.body.style.overflow = '';
    }
  });

  /* ------------------------------------------------------------- hero ---- */
  const slides = $$('.hero-slide');
  if (slides.length > 1) {
    const dots = $$('.hero-dots button');
    let index = 0;
    let timer = null;
    const go = (next) => {
      slides[index].classList.remove('is-active');
      dots[index] && dots[index].classList.remove('is-active');
      index = (next + slides.length) % slides.length;
      slides[index].classList.add('is-active');
      dots[index] && dots[index].classList.add('is-active');
    };
    const start = () => { timer = setInterval(() => go(index + 1), 6000); };
    dots.forEach((dot, i) => dot.addEventListener('click', () => {
      clearInterval(timer); go(i); start();
    }));
    start();
  }

  /* -------------------------------------------------------- accordions --- */
  $$('.acc-head').forEach((head) => {
    head.addEventListener('click', () => {
      const item = head.closest('.acc-item');
      const body = $('.acc-body', item);
      const open = item.classList.toggle('is-open');
      body.style.maxHeight = open ? body.scrollHeight + 'px' : '0px';
    });
  });

  /* ------------------------------------------------------- quantity box -- */
  document.addEventListener('click', (event) => {
    const btn = event.target.closest('[data-qty]');
    if (!btn) return;
    const box = btn.closest('.qty-box');
    const input = $('input', box);
    const step = btn.dataset.qty === 'up' ? 1 : -1;
    const max = parseInt(input.max || '999', 10);
    let value = parseInt(input.value || '1', 10) + step;
    value = Math.max(1, Math.min(value, max || 999));
    input.value = value;
    input.dispatchEvent(new Event('change', { bubbles: true }));
  });

  /* ------------------------------------------------------ product page --- */
  const pd = $('[data-product]');
  if (pd) {
    const readJSON = (id, fallback) => {
      const node = document.getElementById(id);
      if (!node) return fallback;
      try { return JSON.parse(node.textContent); } catch (e) { return fallback; }
    };
    const variantMap = readJSON('variant-data', {});
    const colorBtns = $$('[data-color]', pd);
    const sizeBtns  = $$('[data-size]', pd);
    const variantInput = $('#variant-id', pd);
    const addBtn = $('[data-add-btn]', pd);
    const stockLine = $('[data-stock-line]', pd);
    const qtyInput = $('.qty-box input', pd);
    const mainImg = $('[data-main-img]', pd);
    const strings = readJSON('pd-strings', {});

    let colorId = colorBtns.length ? (colorBtns[0].dataset.color || '0') : '0';
    let sizeId = '0';

    colorBtns.forEach((b) => b.classList.toggle('is-active', b.dataset.color === colorId));

    function stockFor(cId, sId) {
      const entry = variantMap[cId + '-' + sId];
      return entry ? entry.qty : 0;
    }

    function refresh() {
      // sizes availability for the active color
      sizeBtns.forEach((btn) => {
        const qty = stockFor(colorId, btn.dataset.size);
        btn.classList.toggle('is-disabled', qty <= 0);
        if (qty <= 0 && btn.dataset.size === sizeId) {
          sizeId = '0';
          btn.classList.remove('is-active');
        }
      });

      const entry = variantMap[colorId + '-' + sizeId];
      const needsSize = sizeBtns.length > 0 && sizeId === '0';

      if (variantInput) variantInput.value = entry ? entry.id : '';
      const buyInput = document.getElementById('variant-id-buy');
      if (buyInput) buyInput.value = entry ? entry.id : '';
      if (qtyInput && entry) qtyInput.max = entry.qty;

      if (stockLine) {
        if (needsSize) {
          stockLine.className = 'stock-line';
          stockLine.innerHTML = '<span class="dot"></span>' + (strings.choose || '');
        } else if (!entry || entry.qty <= 0) {
          stockLine.className = 'stock-line stock-no';
          stockLine.innerHTML = '<span class="dot"></span>' + (strings.out || '');
        } else if (entry.qty <= 5) {
          stockLine.className = 'stock-line stock-low';
          stockLine.innerHTML = '<span class="dot"></span>' + (strings.only || '') + ' ' + entry.qty + ' ' + (strings.left || '');
        } else {
          stockLine.className = 'stock-line stock-ok';
          stockLine.innerHTML = '<span class="dot"></span>' + (strings.in || '');
        }
      }

      if (addBtn) addBtn.classList.toggle('is-disabled', !entry || entry.qty <= 0);
      $$('[data-buy-btn]', pd).forEach((b) => b.classList.toggle('is-disabled', !entry || entry.qty <= 0));
    }

    colorBtns.forEach((btn) => btn.addEventListener('click', () => {
      colorId = btn.dataset.color;
      colorBtns.forEach((b) => b.classList.toggle('is-active', b === btn));
      const label = $('[data-color-label]', pd);
      if (label) label.textContent = btn.dataset.name || '';
      // swap gallery to this colour's first image
      const firstThumb = $$('.pd-thumb').find((t) => t.dataset.colorId === colorId);
      if (firstThumb) firstThumb.click();
      refresh();
    }));

    sizeBtns.forEach((btn) => btn.addEventListener('click', () => {
      if (btn.classList.contains('is-disabled')) return;
      sizeId = btn.dataset.size;
      sizeBtns.forEach((b) => b.classList.toggle('is-active', b === btn));
      const label = $('[data-size-label]', pd);
      if (label) label.textContent = btn.dataset.name || '';
      refresh();
    }));

    $$('.pd-thumb').forEach((thumb) => thumb.addEventListener('click', () => {
      $$('.pd-thumb').forEach((t) => t.classList.remove('is-active'));
      thumb.classList.add('is-active');
      if (mainImg) mainImg.src = thumb.dataset.full;
    }));

    // keep the "buy now" quantity in sync with the visible qty box
    if (qtyInput) {
      qtyInput.addEventListener('change', () => {
        const hidden = document.querySelector('#buy-now-form input[name="quantity"]');
        if (hidden) hidden.value = qtyInput.value;
      });
    }

    refresh();
  }

  /* ------------------------------------------------- add-to-cart (ajax) -- */
  document.addEventListener('submit', (event) => {
    const form = event.target;
    if (!form.matches('[data-cart-form]')) return;
    if (form.querySelector('[name="buy_now"]')) return; // let buy-now post normally

    const variant = form.querySelector('[name="variant_id"]');
    if (variant && !variant.value) {
      event.preventDefault();
      toast(form.dataset.chooseMsg || 'Choose options first', 'error');
      return;
    }

    event.preventDefault();
    const body = new FormData(form);
    fetch(form.action, {
      method: 'POST',
      body: body,
      headers: { 'X-Requested-With': 'XMLHttpRequest' },
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.ok) {
          toast(data.message, 'success');
          $$('.cart-count').forEach((el) => {
            el.textContent = data.count;
            el.style.display = data.count > 0 ? 'grid' : 'none';
          });
        } else {
          toast(data.message || 'Error', 'error');
        }
      })
      .catch(() => form.submit());
  });

  /* --------------------------------------------------------- shop sort -- */
  const sortSelect = $('[data-sort]');
  if (sortSelect) {
    sortSelect.addEventListener('change', () => {
      const url = new URL(window.location.href);
      url.searchParams.set('sort', sortSelect.value);
      url.searchParams.delete('page');
      window.location.href = url.toString();
    });
  }

  /* ------------------------------------------------------- confirmations - */
  document.addEventListener('submit', (event) => {
    const form = event.target;
    if (form.dataset.confirm && !window.confirm(form.dataset.confirm)) {
      event.preventDefault();
    }
  });

  /* ------------------------------------------------------------ reveal --- */
  const revealables = $$('.reveal');
  if (revealables.length && 'IntersectionObserver' in window) {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('in');
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.08, rootMargin: '0px 0px -40px' });
    revealables.forEach((el) => observer.observe(el));
  } else {
    revealables.forEach((el) => el.classList.add('in'));
  }

  /* --------------------------------------------------- server messages --- */
  $$('[data-server-message]').forEach((el) => {
    toast(el.dataset.serverMessage, el.dataset.serverLevel || 'info');
    el.remove();
  });
})();
