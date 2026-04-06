(function () {
  'use strict';

  const STORAGE_KEY = 'sgs_widget_history_v1';
  const OPEN_KEY    = 'sgs_widget_open';
  var storage = (function () {
    try {
      return window.sessionStorage;
    } catch (_) {
      return window.localStorage;
    }
  })();
  // Clean up old storage keys
  ['acme_widget_history', 'acme_widget_history_v2', 'acme_widget_history_v3', 'acme_widget_history_v4', 'acme_widget_open'].forEach(function (k) {
    storage.removeItem(k);
    window.localStorage.removeItem(k);
  });

  var FAB_LABEL_DEFAULT = 'Chat with Alex';
  var FAB_LABEL_UNREAD = 'New reply — open chat';

  var SUGGESTED_QUESTIONS = [
    'What services does SGS offer?',
    'Where are your office locations?',
    'Tell me about your products',
    'How can I contact SGS?'
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
  btn.type = 'button';
  btn.title = FAB_LABEL_DEFAULT;
  btn.setAttribute('aria-label', FAB_LABEL_DEFAULT);
  btn.innerHTML =
    '<span class="widget-fab-icon">' +
      '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>' +
    '</span>' +
    '<span class="widget-fab-unread-dot" aria-hidden="true"></span>';

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
          '<small>SGS Technologie Assistant</small>' +
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
    '<div class="widget-footer">Powered by <strong>SGS Technologie</strong> AI</div>';

  document.body.appendChild(btn);
  document.body.appendChild(panel);

  var msgList    = panel.querySelector('#wm-list');
  var input      = panel.querySelector('#widget-input');
  var sendBtn    = panel.querySelector('#widget-send');
  var closeBtn   = panel.querySelector('.widget-close');
  var refreshBtn = panel.querySelector('#widget-refresh');
  var statusDot  = panel.querySelector('.widget-status-dot');
  statusDot.setAttribute('aria-label', 'Assistant online');

  var activeStreamController = null;
  var lastKnownModelOnline = true;
  var chatStatusIntervalId = null;

  function updateStatusDotFromModelState() {
    if (statusDot.classList.contains('is-thinking')) return;
    statusDot.classList.toggle('is-offline', !lastKnownModelOnline);
    if (lastKnownModelOnline) {
      statusDot.removeAttribute('title');
      statusDot.setAttribute('aria-label', 'Assistant online');
    } else {
      statusDot.title = 'AI model offline';
      statusDot.setAttribute('aria-label', 'AI model offline');
    }
  }

  function pollChatStatus() {
    fetch('/api/chat-status', { cache: 'no-store' })
      .then(function (r) {
        if (!r.ok) {
          lastKnownModelOnline = false;
          updateStatusDotFromModelState();
          return null;
        }
        return r.json();
      })
      .then(function (j) {
        if (!j) return;
        lastKnownModelOnline = !!j.ollama_ok;
        updateStatusDotFromModelState();
      })
      .catch(function () {
        lastKnownModelOnline = false;
        updateStatusDotFromModelState();
      });
  }

  function startChatStatusPolling() {
    pollChatStatus();
    if (chatStatusIntervalId) clearInterval(chatStatusIntervalId);
    chatStatusIntervalId = setInterval(pollChatStatus, 45000);
  }

  function abortActiveStream() {
    if (activeStreamController) {
      activeStreamController.abort();
      activeStreamController = null;
    }
  }

  // ── Toggle ───────────────────────────────────────────────────────────────────
  function openPanel() {
    panel.classList.add('open');
    btn.classList.add('active');
    btn.classList.remove('widget-fab-unread');
    btn.setAttribute('aria-label', FAB_LABEL_DEFAULT);
    btn.title = FAB_LABEL_DEFAULT;
    storage.setItem(OPEN_KEY, '1');
    pollChatStatus();
  }
  function closePanel() {
    panel.classList.remove('open');
    btn.classList.remove('active');
    storage.removeItem(OPEN_KEY);
  }

  btn.addEventListener('click', function () { panel.classList.contains('open') ? closePanel() : openPanel(); });
  closeBtn.addEventListener('click', closePanel);

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

  function numericPages(pages) {
    if (!Array.isArray(pages)) return [];
    return pages
      .map(function (page) { return parseInt(page, 10); })
      .filter(function (page, index, arr) {
        return Number.isFinite(page) && arr.indexOf(page) === index;
      })
      .sort(function (a, b) { return a - b; });
  }

  function formatPdfPages(pages) {
    var nums = numericPages(pages);
    if (!nums.length) return '';

    var ranges = [];
    var start = nums[0];
    var end = nums[0];

    for (var i = 1; i < nums.length; i++) {
      var page = nums[i];
      if (page === end + 1) {
        end = page;
        continue;
      }
      ranges.push(start === end ? String(start) : (start + '-' + end));
      start = page;
      end = page;
    }
    ranges.push(start === end ? String(start) : (start + '-' + end));

    return ranges.length === 1 && ranges[0].indexOf('-') === -1
      ? ' (p. ' + ranges[0] + ')'
      : ' (pp. ' + ranges.join(', ') + ')';
  }

  function sourceLabel(source) {
    if (source.type === 'website') {
      return source.page_name || source.source_label || 'Website';
    }
    return (source.filename || source.source_label || 'document.pdf') + formatPdfPages(source.pages);
  }

  function appendSources(sources) {
    if (!sources || !sources.length) return;
    var wrap = document.createElement('div');
    wrap.className = 'wm-sources';
    sources.forEach(function (s) {
      var a = document.createElement('a');
      var url;
      if (s.type === 'website') {
        a.className = 'wm-source-tag';
        url = window.location.origin + s.url;
        a.href = url;
        a.innerHTML = escapeHtml(sourceLabel(s)) + ' ' + linkIcon;
      } else {
        a.className = 'wm-source-tag wm-source-pdf';
        url = window.location.origin + (s.url || ('/pdf/' + encodeURIComponent(s.filename)));
        a.href = url;
        a.innerHTML = escapeHtml(sourceLabel(s)) + ' ' + linkIcon;
      }
      if (s.source_id) a.setAttribute('data-source-id', s.source_id);
      if (s.snippet) a.title = s.snippet;
      a.addEventListener('click', function (e) {
        e.preventDefault();
        e.stopPropagation();
        try {
          saveHistory();
        } catch (_) {}
        setTimeout(function () { window.location.href = url; }, 50);
      });
      wrap.appendChild(a);
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
    storage.setItem(STORAGE_KEY, JSON.stringify(entries));
  }

  var linkIcon = '<svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg>';

  function loadHistory() {
    try {
      var entries = JSON.parse(storage.getItem(STORAGE_KEY) || '[]');
      entries.forEach(function (e) {
        var el = document.createElement('div');
        el.className = e.cls;
        el.innerHTML = e.html;
        // Re-attach link icons and click handlers on restored source tags
        if (e.cls.indexOf('wm-sources') !== -1) {
          el.querySelectorAll('.wm-source-tag').forEach(function (a) {
            if (!a.querySelector('svg')) {
              a.innerHTML = a.textContent.trim() + ' ' + linkIcon;
            }
            var url = a.href;
            a.addEventListener('click', function (ev) {
              ev.preventDefault();
              ev.stopPropagation();
              try {
                saveHistory();
              } catch (_) {}
              setTimeout(function () { window.location.href = url; }, 50);
            });
          });
        }
        msgList.appendChild(el);
      });
    } catch (_) {}
  }

  function showWelcome() {
    appendBubble("Hi there! I'm Alex, your SGS Technologie assistant. I can answer questions about our services, products, office locations, and uploaded documents. How can I help?", 'bot', false);
    addSuggestions();
    scroll();
  }

  function resetConversation() {
    abortActiveStream();
    activeStreamController = null;
    btn.classList.remove('widget-fab-thinking', 'widget-fab-unread');
    statusDot.classList.remove('is-thinking');
    btn.setAttribute('aria-label', FAB_LABEL_DEFAULT);
    btn.title = FAB_LABEL_DEFAULT;
    updateStatusDotFromModelState();
    pollChatStatus();
    storage.removeItem(STORAGE_KEY);
    msgList.innerHTML = '';
    showWelcome();
    input.disabled = false;
    sendBtn.disabled = false;
  }

  refreshBtn.addEventListener('click', resetConversation);

  /** Network drops when switching tabs / sleeping the tab often surface as TypeError, not AbortError. */
  function isTransientNetworkError(err) {
    if (!err || err.name === 'AbortError') return false;
    if (typeof TypeError !== 'undefined' && err instanceof TypeError) return true;
    var m = String(err.message || '').toLowerCase();
    if (m.indexOf('network') !== -1) return true;
    if (m.indexOf('failed to fetch') !== -1) return true;
    if (m.indexOf('load failed') !== -1) return true;
    if (m.indexOf('aborted') !== -1 && err.name !== 'AbortError') return true;
    return false;
  }

  // ── Send (streaming) ──────────────────────────────────────────────────────────
  async function send() {
    var question = input.value.trim();
    if (!question) return;

    abortActiveStream();
    var controller = new AbortController();
    var signal = controller.signal;
    activeStreamController = controller;

    // Remove suggestion chips if present
    var allSugg = msgList.querySelectorAll('.wm-suggestions');
    allSugg.forEach(function (el) { el.remove(); });

    input.value = '';
    input.disabled = true;
    sendBtn.disabled = true;

    btn.classList.remove('widget-fab-unread');
    btn.setAttribute('aria-label', FAB_LABEL_DEFAULT);
    btn.title = FAB_LABEL_DEFAULT;
    btn.classList.add('widget-fab-thinking');
    statusDot.classList.add('is-thinking');
    statusDot.title = 'Alex is responding\u2026';
    statusDot.setAttribute('aria-label', 'Alex is responding');

    appendBubble(question, 'user', false);
    scroll();

    var typing = addTyping();

    var streamOk = false;
    try {
      for (var attempt = 0; attempt < 2; attempt++) {
        if (signal.aborted) return;

        var typingRemoved = false;
        var bubble = null;
        var fullText = '';

        try {
          var res = await fetch('/chat/stream', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question: question }),
            signal: signal
          });

          if (signal.aborted) return;

          if (res.status === 429) {
            typing.remove();
            appendBubble('Too many messages \u2014 please wait a moment and try again.', 'bot', false);
            scroll();
            return;
          }

          if (!res.ok) {
            typing.remove();
            appendBubble('Something went wrong. Please try again.', 'bot', false);
            scroll();
            return;
          }

          var reader = res.body.getReader();
          var decoder = new TextDecoder();
          var buffer = '';

          while (true) {
            var chunk = await reader.read();
            if (chunk.done) break;
            if (signal.aborted) return;
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
                  if (!typingRemoved) {
                    typing.remove();
                    typingRemoved = true;
                    bubble = appendBubble('', 'bot', false).bubble;
                  }
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

          if (signal.aborted) return;

          if (!typingRemoved) {
            typing.remove();
            bubble = appendBubble('', 'bot', false).bubble;
          }
          if (!fullText && bubble) {
            bubble.textContent = 'No answer returned.';
          }

          streamOk = true;
          break;
        } catch (err) {
          if (err.name === 'AbortError' || signal.aborted) {
            try { typing.remove(); } catch (_) {}
            return;
          }
          var typingStillVisible = typing && typing.parentNode;
          var canRetry =
            attempt === 0 &&
            typingStillVisible &&
            isTransientNetworkError(err) &&
            !signal.aborted;
          if (canRetry) {
            await new Promise(function (r) { setTimeout(r, 400); });
            continue;
          }
          try { typing.remove(); } catch (_) {}
          if (!signal.aborted) {
            appendBubble('Could not reach the server. Please try again shortly.', 'bot', false);
            scroll();
          }
          return;
        }
      }
    } finally {
      var ownedThisSend = (activeStreamController === controller);
      if (ownedThisSend) {
        activeStreamController = null;
      }
      if (ownedThisSend) {
        btn.classList.remove('widget-fab-thinking');
        statusDot.classList.remove('is-thinking');
        updateStatusDotFromModelState();
        pollChatStatus();
      }
      if (!signal.aborted && ownedThisSend) {
        if (streamOk && !panel.classList.contains('open')) {
          btn.classList.add('widget-fab-unread');
          btn.setAttribute('aria-label', FAB_LABEL_UNREAD);
          btn.title = FAB_LABEL_UNREAD;
        }
        scroll();
        saveHistory();
        input.disabled = false;
        sendBtn.disabled = false;
        input.focus();
      }
    }
  }

  sendBtn.addEventListener('click', send);
  input.addEventListener('keydown', function (e) {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); }
  });

  // ── Init ─────────────────────────────────────────────────────────────────────
  window.addEventListener('pagehide', saveHistory);
  document.addEventListener('visibilitychange', function () {
    if (document.visibilityState === 'visible') pollChatStatus();
  });
  loadHistory();
  if (!msgList.children.length) showWelcome();
  scroll();

  startChatStatusPolling();

  if (storage.getItem(OPEN_KEY)) openPanel();
})();
