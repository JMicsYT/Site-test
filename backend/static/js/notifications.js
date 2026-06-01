/* Уведомления: выпадающая панель в хедере + список из /api/notifications/ */
(function () {
    'use strict';

    var widget = document.querySelector('[data-notif-widget]');
    if (!widget) return;
    var toggleBtn = widget.querySelector('[data-notif-toggle]');
    var panel = widget.querySelector('[data-notif-panel]');
    var listEl = widget.querySelector('[data-notif-list]');
    var markAllBtn = widget.querySelector('[data-notif-mark-all]');
    var countEl = widget.querySelector('[data-notif-count]');
    var loaded = false;

    function getCsrfToken() {
        var m = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
        return m ? decodeURIComponent(m[1]) : '';
    }

    function escapeHtml(s) {
        return String(s || '')
            .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
    }

    function formatTime(iso) {
        try {
            var d = new Date(iso);
            return d.toLocaleString('ru-RU', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' });
        } catch (e) { return ''; }
    }

    function renderList(items) {
        if (!items || !items.length) {
            listEl.innerHTML = '<div class="notif-panel__empty">Пока нет уведомлений</div>';
            return;
        }
        var html = items.map(function (n) {
            var cls = 'notif-item' + (n.is_read ? '' : ' is-unread');
            var href = n.url || '#';
            return '<a class="' + cls + '" href="' + escapeHtml(href) + '" data-id="' + n.id + '">' +
                '<h4 class="notif-item__title">' + escapeHtml(n.title) + '</h4>' +
                (n.body ? '<p class="notif-item__body">' + escapeHtml(n.body) + '</p>' : '') +
                '<div class="notif-item__time">' + formatTime(n.created_at) + '</div>' +
                '</a>';
        }).join('');
        listEl.innerHTML = html;
    }

    function updateCount(n) {
        if (!countEl) return;
        countEl.textContent = n > 0 ? String(n) : '';
        countEl.classList.toggle('is-empty', n <= 0);
    }

    function load() {
        return fetch('/api/notifications/', {
            headers: { 'X-Requested-With': 'XMLHttpRequest', 'Accept': 'application/json' },
            credentials: 'same-origin',
        })
            .then(function (r) { return r.ok ? r.json() : null; })
            .then(function (data) {
                if (!data) return;
                renderList(data.items || []);
                updateCount(data.unread || 0);
                loaded = true;
            })
            .catch(function () {});
    }

    function markAll() {
        fetch('/api/notifications/mark-all-read/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCsrfToken(),
                'X-Requested-With': 'XMLHttpRequest',
            },
            credentials: 'same-origin',
        })
            .then(function () { load(); })
            .catch(function () {});
    }

    toggleBtn.addEventListener('click', function (e) {
        e.stopPropagation();
        var hidden = panel.hasAttribute('hidden');
        if (hidden) {
            panel.removeAttribute('hidden');
            if (!loaded) load();
        } else {
            panel.setAttribute('hidden', '');
        }
    });

    document.addEventListener('click', function (e) {
        if (panel.hasAttribute('hidden')) return;
        if (e.target.closest('[data-notif-widget]')) return;
        panel.setAttribute('hidden', '');
    });

    markAllBtn.addEventListener('click', function (e) {
        e.preventDefault();
        markAll();
    });

    // WebSocket live updates
    function connectWs() {
        try {
            var proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
            var ws = new WebSocket(proto + '//' + location.host + '/ws/notifications/');
            ws.onmessage = function (ev) {
                try {
                    var msg = JSON.parse(ev.data);
                    if (msg && msg.type === 'notification' && msg.data) {
                        if (window.ShoShopToast) {
                            window.ShoShopToast.show(msg.data.title, 'info');
                        }
                        updateCount((parseInt(countEl && countEl.textContent, 10) || 0) + 1);
                        loaded = false; // перезагрузить список при открытии
                    }
                } catch (e) {}
            };
            ws.onclose = function () {
                setTimeout(connectWs, 10000);
            };
            ws.onerror = function () { try { ws.close(); } catch (e) {} };
        } catch (e) {}
    }
    connectWs();
})();
