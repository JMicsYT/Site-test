(function () {
  var widget = document.getElementById('support-widget');
  if (!widget) return;

  var toggle = widget.querySelector('.support-widget__toggle');
  var panel = widget.querySelector('.support-widget__panel');
  var closeBtn = widget.querySelector('.support-widget__close');
  var messagesEl = widget.querySelector('.support-widget__messages');
  var form = widget.querySelector('.support-widget__form');
  var ticketInput = form.querySelector('input[name="ticket_id"]');
  var bodyInput = form.querySelector('textarea[name="body"]');
  var apiUrl = form.getAttribute('action');

  function getFormToken() {
    // Используем ТОЛЬКО токен из скрытого поля формы (Django рендерит его правильной длины).
    // Cookie-токен "замаскирован" (32 символа), и Django 5 отвергает его в заголовке X-CSRFToken.
    var input = form.querySelector('input[name="csrfmiddlewaretoken"]');
    return (input && input.value) || '';
  }

  function formatDate(iso) {
    try {
      var d = new Date(iso);
      return d.toLocaleDateString('ru-RU', {
        day: '2-digit', month: '2-digit', year: 'numeric',
        hour: '2-digit', minute: '2-digit'
      });
    } catch (e) { return iso || ''; }
  }

  function escapeHtml(text) {
    var div = document.createElement('div');
    div.textContent = text || '';
    return div.innerHTML.replace(/\n/g, '<br>');
  }

  function renderMessages(data) {
    var html = '';
    // Баннер статуса — всегда сверху, если тикет завершён
    if (data.status === 'completed') {
      html += '<div class="support-widget__status support-widget__status--done">' +
        '<strong>Обращение завершено</strong>' +
        '<span>Администратор закрыл это обращение. Чтобы задать новый вопрос — нажмите кнопку ниже.</span>' +
        '</div>';
    }
    if (!data.messages || !data.messages.length) {
      if (!html) {
        html = '<p class="support-widget__empty">Напишите первое сообщение — мы ответим в ближайшее время.</p>';
      }
      messagesEl.innerHTML = html;
      return;
    }
    html += data.messages.map(function (m) {
      var className = m.is_staff
        ? 'support-widget__msg support-widget__msg--staff'
        : 'support-widget__msg support-widget__msg--user';
      var who = m.is_staff
        ? ('Поддержка' + (m.author ? ' (' + escapeHtml(m.author) + ')' : ''))
        : 'Вы';
      return '<div class="' + className + '">' +
        '<div class="support-widget__msg-meta">' + who + ' · ' + formatDate(m.created_at) + '</div>' +
        '<div class="support-widget__msg-body">' + escapeHtml(m.body) + '</div></div>';
    }).join('');
    messagesEl.innerHTML = html;
    messagesEl.scrollTop = messagesEl.scrollHeight;
  }

  function setCompletedMode() {
    form.style.display = 'none';
    var oldBtn = widget.querySelector('.support-widget__new-ticket');
    if (oldBtn) return;
    var wrap = widget.querySelector('.support-widget__form-wrap');
    if (!wrap) return;
    var btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'btn btn-primary btn-block support-widget__new-ticket';
    btn.textContent = 'Задать новый вопрос';
    btn.addEventListener('click', function () {
      // Сбрасываем ticket_id и включаем форму — следующее сообщение создаст новый тикет
      ticketInput.value = '';
      form.style.display = '';
      btn.remove();
      // Плейсхолдер в переписке
      messagesEl.innerHTML = '<p class="support-widget__empty">Опишите ваш вопрос — мы ответим в ближайшее время.</p>';
      setTimeout(function () { try { bodyInput.focus(); } catch (e) {} }, 30);
    });
    wrap.appendChild(btn);
  }

  function setActiveMode() {
    var oldBtn = widget.querySelector('.support-widget__new-ticket');
    if (oldBtn) oldBtn.remove();
    form.style.display = '';
  }

  function loadChat() {
    messagesEl.innerHTML = '<p class="support-widget__loading">Загрузка…</p>';
    fetch(apiUrl, {
      method: 'GET',
      headers: { 'Accept': 'application/json', 'X-Requested-With': 'XMLHttpRequest' },
      credentials: 'same-origin'
    })
      .then(function (r) {
        if (!r.ok) throw new Error('HTTP ' + r.status);
        return r.json();
      })
      .then(function (data) {
        ticketInput.value = data.ticket_id || '';
        renderMessages(data);
        if (data.status === 'completed') {
          setCompletedMode();
        } else {
          setActiveMode();
        }
      })
      .catch(function (err) {
        messagesEl.innerHTML = '<p class="support-widget__empty">Не удалось загрузить чат. Попробуйте позже.</p>';
        console.error('[support] load failed:', err);
      });
  }

  function openPanel() {
    panel.removeAttribute('hidden');
    loadChat();
    setTimeout(function () { try { bodyInput.focus(); } catch (e) {} }, 50);
  }

  function closePanel() {
    panel.setAttribute('hidden', '');
  }

  toggle.addEventListener('click', function () {
    if (panel.hasAttribute('hidden')) openPanel(); else closePanel();
  });

  if (closeBtn) closeBtn.addEventListener('click', closePanel);

  form.addEventListener('submit', function (e) {
    e.preventDefault();
    var body = (bodyInput.value || '').trim();
    if (!body) return;

    // Используем FormData(form) — сразу возьмёт csrfmiddlewaretoken, ticket_id, body.
    // Django проверит CSRF по полю csrfmiddlewaretoken — заголовок X-CSRFToken
    // специально НЕ передаём, чтобы не конфликтовать с cookie-токеном.
    var fd = new FormData(form);

    var submitBtn = form.querySelector('button[type="submit"]');
    if (submitBtn) submitBtn.disabled = true;

    fetch(apiUrl, {
      method: 'POST',
      body: fd,
      headers: { 'X-Requested-With': 'XMLHttpRequest' },
      credentials: 'same-origin'
    })
      .then(function (r) {
        return r.json().then(function (data) { return { ok: r.ok, data: data }; });
      })
      .then(function (res) {
        if (res.ok && res.data && res.data.ok) {
          ticketInput.value = res.data.ticket_id;
          bodyInput.value = '';
          loadChat();
        } else {
          var msg = (res.data && res.data.error) || 'Не удалось отправить сообщение. Обновите страницу и попробуйте снова.';
          alert(msg);
        }
      })
      .catch(function (err) {
        console.error('[support] send failed:', err);
        alert('Сетевая ошибка при отправке. Попробуйте позже.');
      })
      .then(function () {
        if (submitBtn) submitBtn.disabled = false;
      });
  });

  // Enter — отправить; Shift+Enter — перенос строки
  bodyInput.addEventListener('keydown', function (e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      form.requestSubmit ? form.requestSubmit() : form.dispatchEvent(new Event('submit', { cancelable: true }));
    }
  });
})();
