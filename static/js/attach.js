/* RGS TOWER — ticket attachments + voice note.
   Shared by the storefront and the dashboard (both include this file). */
(function () {
  'use strict';
  const $  = (sel, root) => (root || document).querySelector(sel);
  const $$ = (sel, root) => Array.from((root || document).querySelectorAll(sel));

  /* --------------------------------------------- the conversation itself */
  /* the scrolling pane this element belongs to, so the newest message stays
     in view when the box below it grows */
  const paneFor = (el) => {
    const shell = el.closest('.chat-shell');
    return shell ? shell.querySelector('[data-chat-scroll]') : null;
  };
  const keepAtBottom = (pane) => { if (pane) pane.scrollTop = pane.scrollHeight; };

  $$('[data-chat-scroll]').forEach((pane) => {
    /* open on the newest message, the way a chat app does */
    const toBottom = () => { pane.scrollTop = pane.scrollHeight; };
    toBottom();
    /* images finish loading after the first paint and push everything down */
    $$('img', pane).forEach((img) => {
      if (!img.complete) img.addEventListener('load', toBottom, { once: true });
    });
    window.addEventListener('load', toBottom, { once: true });
  });

  $$('[data-chat-input]').forEach((input) => {
    const form = input.closest('form');
    const pane = paneFor(input);
    const grow = () => {
      input.style.height = 'auto';
      input.style.height = Math.min(input.scrollHeight, 140) + 'px';
      keepAtBottom(pane);
    };
    input.addEventListener('input', grow);
    grow();

    /* Enter sends on a real keyboard; on a phone it stays a new line */
    input.addEventListener('keydown', (event) => {
      if (event.key !== 'Enter' || event.shiftKey || event.isComposing) return;
      if (!window.matchMedia('(min-width: 900px)').matches) return;
      event.preventDefault();
      if (form && form.requestSubmit) form.requestSubmit();
      else if (form) form.submit();
    });
  });

  /* ------------------------------------------------- voice notes -------- */
  /* our own little player: the browser's default one collapses to its
     overflow button inside a bubble that sizes itself to its content */
  const clock = (seconds) => {
    const s = Math.max(0, Math.round(seconds || 0));
    return Math.floor(s / 60) + ':' + String(s % 60).padStart(2, '0');
  };

  $$('[data-audio]').forEach((box) => {
    const sound = $('[data-audio-el]', box);
    const toggle = $('[data-audio-toggle]', box);
    const bar = $('[data-audio-bar]', box);
    const fill = $('[data-audio-fill]', box);
    const label = $('[data-audio-time]', box);
    if (!sound || !toggle) return;

    const span = () => (isFinite(sound.duration) && sound.duration > 0 ? sound.duration : 0);
    const showLength = () => { if (label) label.textContent = clock(span()); };
    const reset = () => {
      box.classList.remove('is-playing');
      if (fill) fill.style.width = '0%';
      showLength();
    };

    /* a webm recorded in the browser reports Infinity until it is seeked once */
    const measure = () => {
      if (sound.duration !== Infinity) { showLength(); return; }
      const settle = () => {
        sound.removeEventListener('timeupdate', settle);
        sound.currentTime = 0;
        showLength();
      };
      sound.addEventListener('timeupdate', settle);
      sound.currentTime = 1e101;
    };
    sound.addEventListener('loadedmetadata', measure);
    sound.addEventListener('durationchange', showLength);
    sound.addEventListener('timeupdate', () => {
      if (sound.currentTime > 1e6) return;               // the seek trick above
      const total = span();
      if (fill) fill.style.width = total ? (sound.currentTime / total) * 100 + '%' : '0%';
      if (label) label.textContent = clock(sound.currentTime);
    });
    sound.addEventListener('ended', reset);
    sound.addEventListener('pause', () => box.classList.remove('is-playing'));
    sound.addEventListener('play', () => {
      $$('[data-audio]').forEach((other) => {
        if (other === box) return;
        const item = $('[data-audio-el]', other);
        if (item && !item.paused) item.pause();          // one at a time
      });
      box.classList.add('is-playing');
    });

    toggle.addEventListener('click', () => {
      if (sound.paused) {
        const playing = sound.play();
        if (playing && playing.catch) playing.catch(() => {});
      } else {
        sound.pause();
      }
    });

    if (bar) {
      const seek = (event) => {
        const rect = bar.getBoundingClientRect();
        const total = span();
        if (!rect.width || !total) return;
        let point = (event.clientX - rect.left) / rect.width;
        /* the bar fills from the play button outwards, so it runs the other
           way round in Arabic */
        if (getComputedStyle(bar).direction === 'rtl') point = 1 - point;
        sound.currentTime = Math.min(Math.max(point, 0), 1) * total;
      };
      bar.addEventListener('click', seek);
    }

    /* the recorder drops a blob in later */
    sound.addEventListener('emptied', reset);
    showLength();
  });

  /* ------------------------------- ticket attachments + voice note ------ */
  $$('[data-attach]').forEach((box) => {
    const input = $('[data-attach-input]', box);
    const list = $('[data-attach-list]', box);
    const counter = $('[data-attach-count]', box);
    const startBtn = $('[data-record-start]', box);
    const stopBtn = $('[data-record-stop]', box);
    const timeEl = $('[data-record-time]', box);
    const voiceBox = $('[data-voice-box]', box);
    const player = $('[data-voice-player]', box);
    const clearBtn = $('[data-voice-clear]', box);
    const errorEl = $('[data-record-error]', box);
    const form = box.closest('form');

    /* what the visitor picked */
    if (input && list) {
      input.addEventListener('change', () => {
        list.innerHTML = '';
        const files = Array.from(input.files || []);
        list.hidden = files.length === 0;
        if (counter) {
          counter.textContent = files.length;
          counter.hidden = files.length === 0;
        }
        keepAtBottom(paneFor(box));
        files.forEach((file) => {
          const chip = document.createElement('span');
          chip.className = 'attach-chip';
          if (file.type.startsWith('image/')) {
            const img = document.createElement('img');
            img.src = URL.createObjectURL(file);
            chip.appendChild(img);
          }
          const name = document.createElement('span');
          name.textContent = file.name;
          chip.appendChild(name);
          list.appendChild(chip);
        });
      });
    }

    /* the voice note: recorded here, sent with the form as `voice` */
    let recorder = null;
    let chunks = [];
    let ticker = null;
    let blob = null;

    const canRecord = !!(navigator.mediaDevices && window.MediaRecorder);
    if (!canRecord && startBtn) {
      startBtn.hidden = true;
      if (errorEl) errorEl.hidden = false;
    }

    const showTime = (seconds) => {
      if (timeEl) timeEl.textContent = Math.floor(seconds / 60) + ':' + String(seconds % 60).padStart(2, '0');
    };

    const stopTracks = () => {
      if (recorder && recorder.stream) recorder.stream.getTracks().forEach((track) => track.stop());
    };

    if (startBtn && canRecord) {
      startBtn.addEventListener('click', async () => {
        try {
          const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
          chunks = [];
          recorder = new MediaRecorder(stream);
          recorder.ondataavailable = (event) => { if (event.data.size) chunks.push(event.data); };
          recorder.onstop = () => {
            blob = new Blob(chunks, { type: recorder.mimeType || 'audio/webm' });
            if (player) player.src = URL.createObjectURL(blob);
            if (voiceBox) voiceBox.hidden = false;
            keepAtBottom(paneFor(box));
            stopTracks();
          };
          recorder.start();
          startBtn.hidden = true;
          if (stopBtn) stopBtn.hidden = false;
          let seconds = 0;
          showTime(0);
          ticker = setInterval(() => {
            seconds += 1;
            showTime(seconds);
            if (seconds >= 180 && stopBtn) stopBtn.click();   // 3 دقايق كحد أقصى
          }, 1000);
        } catch (e) {
          if (errorEl) errorEl.hidden = false;
        }
      });
    }

    if (stopBtn) {
      stopBtn.addEventListener('click', () => {
        if (recorder && recorder.state !== 'inactive') recorder.stop();
        clearInterval(ticker);
        stopBtn.hidden = true;
        if (startBtn) startBtn.hidden = false;
      });
    }

    if (clearBtn) {
      clearBtn.addEventListener('click', () => {
        blob = null;
        if (player) player.removeAttribute('src');
        if (voiceBox) voiceBox.hidden = true;
      });
    }

    /* attach the recording to the form right before it is submitted */
    if (form) {
      form.addEventListener('submit', () => {
        if (!blob) return;
        const data = new DataTransfer();
        data.items.add(new File([blob], 'voice-note.webm', { type: blob.type || 'audio/webm' }));
        let hidden = $('[data-voice-file]', form);
        if (!hidden) {
          hidden = document.createElement('input');
          hidden.type = 'file';
          hidden.name = 'voice';
          hidden.hidden = true;
          hidden.setAttribute('data-voice-file', '');
          form.appendChild(hidden);
        }
        hidden.files = data.files;
      });
    }
  });
})();
