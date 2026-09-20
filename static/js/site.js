/* RGS TOWER — storefront behaviour */
(function () {
  'use strict';

  const $  = (sel, root) => (root || document).querySelector(sel);
  const $$ = (sel, root) => Array.from((root || document).querySelectorAll(sel));

  /* The store is dark only — drop the theme some visitors saved before. */
  try { localStorage.removeItem('rgs-theme'); } catch (e) { /* storage unavailable */ }

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

  /* ------------------------------------------------------ account menu -- */
  document.addEventListener('click', (event) => {
    const toggle = event.target.closest('[data-menu-toggle]');
    $$('[data-menu].is-open').forEach((menu) => {
      if (!toggle || !menu.contains(toggle)) {
        menu.classList.remove('is-open');
        const btn = $('[data-menu-toggle]', menu);
        btn && btn.setAttribute('aria-expanded', 'false');
      }
    });
    if (toggle) {
      const menu = toggle.closest('[data-menu]');
      const open = menu.classList.toggle('is-open');
      toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
    }
  });
  document.addEventListener('keydown', (event) => {
    if (event.key !== 'Escape') return;
    $$('[data-menu].is-open').forEach((menu) => menu.classList.remove('is-open'));
  });

  /* --------------------------------------------------- show password ---- */
  document.addEventListener('click', (event) => {
    const btn = event.target.closest('[data-pass-toggle]');
    if (!btn) return;
    const input = $('input', btn.closest('.pass-wrap'));
    if (input) input.type = input.type === 'password' ? 'text' : 'password';
  });

  /* ------------------------------------------------------- copy link ---- */
  document.addEventListener('click', (event) => {
    const btn = event.target.closest('[data-copy]');
    if (!btn) return;
    const text = btn.dataset.copy;
    const done = () => toast(btn.dataset.copied || 'Copied', 'success');
    if (navigator.clipboard && window.isSecureContext) {
      navigator.clipboard.writeText(text).then(done).catch(() => window.prompt('', text));
    } else {
      const area = document.createElement('textarea');
      area.value = text; area.style.position = 'fixed'; area.style.opacity = '0';
      document.body.appendChild(area); area.select();
      try { document.execCommand('copy'); done(); } catch (e) { window.prompt('', text); }
      area.remove();
    }
  });

  /* ------------------------------------------ checkout button label ---- */
  const submitBtn = $('[data-checkout-submit]');
  if (submitBtn) {
    const label = $('[data-submit-label]', submitBtn);
    $$('input[name="payment_method"]').forEach((radio) => {
      radio.addEventListener('change', () => {
        if (!radio.checked || !label) return;
        label.textContent = radio.value === 'paypal' ? submitBtn.dataset.labelPaypal : submitBtn.dataset.labelCod;
      });
    });
  }

  /* -------------------------------------------------- work lightbox ----- */
  const gallery = $('[data-gallery]');
  const box = $('[data-lightbox]');
  if (gallery && box) {
    const items = $$('.gal-item', gallery);
    const stage = $('[data-lb-stage]', box);
    const caption = $('[data-lb-caption]', box);
    const count = $('[data-lb-count]', box);
    let current = 0;
    let lastFocus = null;

    const render = () => {
      const item = items[current];
      const kind = item.dataset.kind;
      const src = item.dataset.src;
      stage.innerHTML = '';
      let node;
      if (kind === 'image') {
        node = document.createElement('img');
        node.src = src; node.alt = item.dataset.caption || '';
      } else if (kind === 'video') {
        node = document.createElement('video');
        node.src = src; node.controls = true; node.autoplay = true; node.playsInline = true;
      } else {
        node = document.createElement('iframe');
        node.src = src;
        node.allow = 'autoplay; fullscreen; picture-in-picture; encrypted-media';
        node.allowFullscreen = true;
        node.title = item.dataset.caption || 'video';
      }
      stage.appendChild(node);
      caption.textContent = item.dataset.caption || '';
      count.textContent = (current + 1) + ' / ' + items.length;
    };
    const open = (index) => {
      current = index; lastFocus = document.activeElement;
      box.hidden = false; document.body.style.overflow = 'hidden';
      render();
      const close = $('[data-lb-close]', box); close && close.focus();
    };
    const close = () => {
      box.hidden = true; stage.innerHTML = ''; document.body.style.overflow = '';
      lastFocus && lastFocus.focus && lastFocus.focus();
    };
    const step = (dir) => { current = (current + dir + items.length) % items.length; render(); };
    const rtl = document.documentElement.dir === 'rtl';

    items.forEach((item, i) => item.addEventListener('click', () => open(i)));
    $('[data-lb-close]', box).addEventListener('click', close);
    $('[data-lb-prev]', box).addEventListener('click', () => step(-1));
    $('[data-lb-next]', box).addEventListener('click', () => step(1));
    box.addEventListener('click', (event) => { if (event.target === box) close(); });
    document.addEventListener('keydown', (event) => {
      if (box.hidden) return;
      if (event.key === 'Escape') close();
      if (event.key === 'ArrowRight') step(rtl ? -1 : 1);
      if (event.key === 'ArrowLeft') step(rtl ? 1 : -1);
    });
    if (items.length < 2) $$('.lb-nav', box).forEach((btn) => { btn.hidden = true; });
  }
})();
