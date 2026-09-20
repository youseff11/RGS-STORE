/* RGS TOWER — ticket attachments + voice note.
   Shared by the storefront and the dashboard (both include this file). */
(function () {
  'use strict';
  const $  = (sel, root) => (root || document).querySelector(sel);
  const $$ = (sel, root) => Array.from((root || document).querySelectorAll(sel));

  /* ------------------------------- ticket attachments + voice note ------ */
  $$('[data-attach]').forEach((box) => {
    const input = $('[data-attach-input]', box);
    const list = $('[data-attach-list]', box);
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
