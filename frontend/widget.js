(function () {
  'use strict';

  const STORAGE_KEY = 'acme_widget_history_v4';
  const OPEN_KEY    = 'acme_widget_open';
  // Clean up old storage keys
  ['acme_widget_history', 'acme_widget_history_v2', 'acme_widget_history_v3'].forEach(function (k) {
    sessionStorage.removeItem(k);
  });

  var SUGGESTED_QUESTIONS = [
    'What services do you offer?',
    'Tell me about your pricing',
    'Who is on the leadership team?',
    'How can I contact you?'
  ];

  // ── Markdown renderer (lightweight) ────────────────────────────────────────
  function renderMarkdown(text) {
    var html = escapeHtml(text);
    // Bold: **text**
    html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    // Italic: *text* (but not inside bold)
    html = html.replace(/(?<!\*)\*([^*]+?)\*(?!\*)/g, '<em>$1</em>');
    // Inline code: `code`
    html = html.replace(/`([^`]+?)`/g, '<code>$1</code>');
    // Unordered list items: - item or * item (at line start)
    html = html.replace(/^[\-\*]\s+(.+)$/gm, '<li>$1</li>');
    // Wrap consecutive <li> in <ul>
    html = html.replace(/((?:<li>.*?<\/li>\n?)+)/g, '<ul>$1</ul>');
    // Numbered list items: 1. item
    html = html.replace(/^\d+\.\s+(.+)$/gm, '<li>$1</li>');
    html = html.replace(/((?:<li>.*?<\/li>\n?)+)/g, function (match) {
      // Only wrap if not already wrapped
      if (match.indexOf('<ul>') === -1) return '<ul>' + match + '</ul>';
      return match;
    });
    // Line breaks
    html = html.replace(/\n/g, '<br>');
    // Clean up <br> inside lists
    html = html.replace(/<br><ul>/g, '<ul>');
    html = html.replace(/<\/ul><br>/g, '</ul>');
    html = html.replace(/<br><\/li>/g, '</li>');
    html = html.replace(/<li><br>/g, '<li>');
    return html;
  }

  // ── Build DOM ────────────────────────────────────────────────────────────────
  var btn = document.createElement('button');
  btn.id = 'chat-widget-btn';
  btn.title = 'Chat with Alex';
  btn.innerHTML = '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>';

  var panel = document.createElement('div');
  panel.id = 'chat-widget-panel';
  panel.innerHTML =
    '<div class="widget-header">' +
      '<div class="widget-header-info">' +
        '<div class="widget-avatar-wrap">' +
          '<div class="widget-avatar">A</div>' +
          '<span class="widget-status-dot"></span>' +
        '</div>' +
        '<div>' +
          '<h4>Alex</h4>' +
          '<small>SGS Technologies Assistant</small>' +
        '</div>' +
      '</div>' +
      '<div class="widget-header-actions">' +
        '<button class="widget-icon-btn" id="widget-refresh" title="New conversation">' +
          '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M1 4v6h6M23 20v-6h-6"/><path d="M20.49 9A9 9 0 0 0 5.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 0 1 3.51 15"/></svg>' +
        '</button>' +
        '<button class="widget-icon-btn widget-close" title="Close">' +
          '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>' +
        '</button>' +
      '</div>' +
    '</div>' +
    '<div class="widget-messages" id="wm-list"></div>' +
    '<div class="widget-input-row">' +
      '<input id="widget-input" type="text" placeholder="Ask me anything..." autocomplete="off">' +
      '<button id="widget-send" title="Send">' +
        '<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M2 21l21-9L2 3v7l15 2-15 2z"/></svg>' +
      '</button>' +
    '</div>' +
    '<div class="widget-footer">Powered by <strong>SGS Technologies</strong> AI</div>';

  document.body.appendChild(btn);
  document.body.appendChild(panel);

  var msgList    = panel.querySelector('#wm-list');
  var input      = panel.querySelector('#widget-input');
  var sendBtn    = panel.querySelector('#widget-send');
  var closeBtn   = panel.querySelector('.widget-close');
  var refreshBtn = panel.querySelector('#widget-refresh');

  // ── Toggle ───────────────────────────────────────────────────────────────────
  function openPanel()  { panel.classList.add('open'); btn.classList.add('active'); localStorage.setItem(OPEN_KEY, '1'); }
  function closePanel() { panel.classList.remove('open'); btn.classList.remove('active'); localStorage.removeItem(OPEN_KEY); }

  btn.addEventListener('click', function () { panel.classList.contains('open') ? closePanel() : openPanel(); });
  closeBtn.addEventListener('click', closePanel);
  refreshBtn.addEventListener('click', function () {
    sessionStorage.removeItem(STORAGE_KEY);
    msgList.innerHTML = '';
    showWelcome();
  });

  if (localStorage.getItem(OPEN_KEY)) openPanel();

  // ── Message helpers ──────────────────────────────────────────────────────────
  function escapeHtml(str) {
    return str.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  }

  function appendBubble(text, role, useMarkdown) {
    var wrap = document.createElement('div');
    wrap.className = 'wm-row wm-row-' + role;

    if (role === 'bot') {
      var avatar = document.createElement('div');
      avatar.className = 'wm-bot-avatar';
      avatar.textContent = 'A';
      wrap.appendChild(avatar);
    }

    var bubble = document.createElement('div');
    bubble.className = 'wm-bubble wm-' + role;
    if (useMarkdown && role === 'bot') {
      bubble.innerHTML = renderMarkdown(text);
    } else {
      bubble.innerHTML = escapeHtml(text).replace(/\n/g, '<br>');
    }
    wrap.appendChild(bubble);

    msgList.appendChild(wrap);
    return { wrap: wrap, bubble: bubble };
  }

  function appendSources(sources) {
    if (!sources || !sources.length) return;
    var wrap = document.createElement('div');
    wrap.className = 'wm-sources';
    sources.forEach(function (s) {
      if (s.type === 'website') {
        var a = document.createElement('a');
        a.className = 'wm-source-tag';
        a.href = s.url;
        a.innerHTML = escapeHtml(s.page_name);
        wrap.appendChild(a);
      } else {
        var a = document.createElement('a');
        a.className = 'wm-source-tag wm-source-pdf';
        a.href = s.url || ('/pdf/' + encodeURIComponent(s.filename));
        a.target = '_blank';
        a.rel = 'noopener noreferrer';
        a.innerHTML = '<svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg> ' + escapeHtml(s.filename);
        wrap.appendChild(a);
      }
    });
    msgList.appendChild(wrap);
  }

  function addTyping() {
    var wrap = document.createElement('div');
    wrap.className = 'wm-row wm-row-bot';
    var avatar = document.createElement('div');
    avatar.className = 'wm-bot-avatar';
    avatar.textContent = 'A';
    var dots = document.createElement('div');
    dots.className = 'wm-typing';
    dots.innerHTML = '<span></span><span></span><span></span>';
    wrap.appendChild(avatar);
    wrap.appendChild(dots);
    msgList.appendChild(wrap);
    scroll();
    return wrap;
  }

  function addSuggestions() {
    var wrap = document.createElement('div');
    wrap.className = 'wm-suggestions';
    SUGGESTED_QUESTIONS.forEach(function (q) {
      var chip = document.createElement('button');
      chip.className = 'wm-suggestion-chip';
      chip.textContent = q;
      chip.addEventListener('click', function () {
        // Remove all suggestion containers
        var allSugg = msgList.querySelectorAll('.wm-suggestions');
        allSugg.forEach(function (el) { el.remove(); });
        input.value = q;
        send();
      });
      wrap.appendChild(chip);
    });
    msgList.appendChild(wrap);
  }

  function scroll() { msgList.scrollTop = msgList.scrollHeight; }

  // ── History ──────────────────────────────────────────────────────────────────
  function saveHistory() {
    var entries = [];
    msgList.querySelectorAll('.wm-row, .wm-sources').forEach(function (el) {
      entries.push({ cls: el.className, html: el.innerHTML });
    });
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(entries));
  }

  function loadHistory() {
    try {
      var entries = JSON.parse(sessionStorage.getItem(STORAGE_KEY) || '[]');
      entries.forEach(function (e) {
        var el = document.createElement('div');
        el.className = e.cls;
        el.innerHTML = e.html;
        msgList.appendChild(el);
      });
    } catch (_) {}
  }

  function showWelcome() {
    appendBubble("Hi there! I'm Alex, your SGS Technologies assistant. I can answer questions about our services, team, pricing, and uploaded documents. How can I help?", 'bot', false);
    addSuggestions();
    scroll();
  }

  // ── Send (streaming) ──────────────────────────────────────────────────────────
  async function send() {
    var question = input.value.trim();
    if (!question) return;

    // Remove suggestion chips if present
    var allSugg = msgList.querySelectorAll('.wm-suggestions');
    allSugg.forEach(function (el) { el.remove(); });

    input.value = '';
    input.disabled = true;
    sendBtn.disabled = true;

    appendBubble(question, 'user', false);
    scroll();

    var typing = addTyping();

    try {
      var res = await fetch('/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: question })
      });

      typing.remove();

      if (res.status === 429) {
        appendBubble('Too many messages \u2014 please wait a moment and try again.', 'bot', false);
        scroll();
        saveHistory();
        input.disabled = false;
        sendBtn.disabled = false;
        input.focus();
        return;
      }

      if (!res.ok) {
        appendBubble('Something went wrong. Please try again.', 'bot', false);
        scroll();
        saveHistory();
        input.disabled = false;
        sendBtn.disabled = false;
        input.focus();
        return;
      }

      // Create empty bot bubble for streaming
      var result = appendBubble('', 'bot', false);
      var bubble = result.bubble;
      var fullText = '';

      var reader = res.body.getReader();
      var decoder = new TextDecoder();
      var buffer = '';

      while (true) {
        var chunk = await reader.read();
        if (chunk.done) break;
        buffer += decoder.decode(chunk.value, { stream: true });

        var lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (var i = 0; i < lines.length; i++) {
          var line = lines[i].trim();
          if (!line.startsWith('data: ')) continue;
          var payload = line.slice(6);
          if (payload === '[DONE]') continue;

          try {
            var evt = JSON.parse(payload);
            if (evt.type === 'token') {
              fullText += evt.content;
              bubble.innerHTML = renderMarkdown(fullText);
              scroll();
            } else if (evt.type === 'sources') {
              appendSources(evt.sources);
              scroll();
            } else if (evt.type === 'error') {
              fullText = evt.content;
              bubble.innerHTML = renderMarkdown(fullText);
              scroll();
            }
          } catch (_) {}
        }
      }

      if (!fullText) {
        bubble.textContent = 'No answer returned.';
      }

    } catch (err) {
      typing.remove();
      appendBubble('Could not reach the server. Please try again shortly.', 'bot', false);
    }

    scroll();
    saveHistory();
    input.disabled = false;
    sendBtn.disabled = false;
    input.focus();
  }

  sendBtn.addEventListener('click', send);
  input.addEventListener('keydown', function (e) {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); }
  });

  // ── Init ─────────────────────────────────────────────────────────────────────
  loadHistory();
  if (!msgList.children.length) showWelcome();
  scroll();
})();
