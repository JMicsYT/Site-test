/* Смарт-поиск с автодополнением: товары + категории, подсветка совпадений,
   клавиатура (↑/↓/Enter/Esc). */
(function () {
    'use strict';

    document.addEventListener('DOMContentLoaded', function () {
        var input = document.querySelector('[data-global-search]');
        var box = document.querySelector('[data-search-suggestions]');
        if (!input || !box) return;

        var timer = null;
        var activeIdx = -1;
        var items = [];

        input.setAttribute('autocomplete', 'off');
        input.setAttribute('role', 'combobox');
        input.setAttribute('aria-autocomplete', 'list');
        box.setAttribute('role', 'listbox');

        input.addEventListener('input', function () {
            var q = input.value.trim();
            if (timer) clearTimeout(timer);
            if (q.length < 2) { closeBox(); return; }
            timer = setTimeout(function () { fetchSuggestions(q); }, 180);
        });

        input.addEventListener('keydown', function (e) {
            if (!items.length) return;
            if (e.key === 'ArrowDown') {
                e.preventDefault();
                setActive((activeIdx + 1) % items.length);
            } else if (e.key === 'ArrowUp') {
                e.preventDefault();
                setActive((activeIdx - 1 + items.length) % items.length);
            } else if (e.key === 'Enter') {
                if (activeIdx >= 0 && items[activeIdx]) {
                    e.preventDefault();
                    window.location.href = items[activeIdx].href;
                }
            } else if (e.key === 'Escape') {
                closeBox();
            }
        });

        input.addEventListener('blur', function () {
            setTimeout(closeBox, 180);
        });

        input.addEventListener('focus', function () {
            if (box.childElementCount > 0) box.classList.add('visible');
        });

        function closeBox() {
            box.classList.remove('visible');
            activeIdx = -1;
            items = [];
        }

        function setActive(idx) {
            activeIdx = idx;
            var nodes = box.querySelectorAll('.suggestion-item');
            nodes.forEach(function (n, i) {
                n.classList.toggle('is-active', i === idx);
            });
            var chosen = nodes[idx];
            if (chosen && chosen.scrollIntoView) {
                chosen.scrollIntoView({ block: 'nearest' });
            }
        }

        function escapeHtml(s) {
            return String(s || '')
                .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
                .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
        }

        function highlight(text, query) {
            var safe = escapeHtml(text);
            if (!query) return safe;
            try {
                var esc = query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
                return safe.replace(
                    new RegExp('(' + esc + ')', 'ig'),
                    '<mark>$1</mark>'
                );
            } catch (_) { return safe; }
        }

        function render(data) {
            var q = data.query || '';
            var html = '';
            items = [];

            if (data.categories && data.categories.length) {
                html += '<div class="suggestion-group">Категории</div>';
                data.categories.forEach(function (c) {
                    items.push({ href: c.url });
                    html += '<a href="' + escapeHtml(c.url) + '" class="suggestion-item suggestion-item--cat">' +
                        '<span class="suggestion-icon" aria-hidden="true">◉</span>' +
                        '<span class="suggestion-name">' + highlight(c.name, q) + '</span>' +
                        '</a>';
                });
            }
            if (data.products && data.products.length) {
                html += '<div class="suggestion-group">Товары</div>';
                data.products.forEach(function (p) {
                    items.push({ href: p.url });
                    var img = p.image
                        ? '<img src="' + escapeHtml(p.image) + '" alt="" class="suggestion-thumb">'
                        : '<span class="suggestion-icon" aria-hidden="true">🛍</span>';
                    html += '<a href="' + escapeHtml(p.url) + '" class="suggestion-item">' +
                        img +
                        '<span class="suggestion-body">' +
                            '<span class="suggestion-name">' + highlight(p.name, q) + '</span>' +
                            '<span class="suggestion-meta">' + escapeHtml(p.type) + (p.category ? ' · ' + escapeHtml(p.category) : '') + '</span>' +
                        '</span>' +
                        '<span class="suggestion-price">' + escapeHtml(p.price) + ' ₽</span>' +
                        '</a>';
                });
            }
            if (!html) {
                closeBox();
                return;
            }
            box.innerHTML = html;
            box.classList.add('visible');
            activeIdx = -1;
        }

        function fetchSuggestions(query) {
            fetch('/api/catalog/autocomplete/?q=' + encodeURIComponent(query), {
                headers: { 'X-Requested-With': 'XMLHttpRequest' },
                credentials: 'same-origin',
            })
                .then(function (r) { return r.ok ? r.json() : null; })
                .then(function (data) {
                    if (!data) { closeBox(); return; }
                    render(data);
                })
                .catch(function () { closeBox(); });
        }
    });
})();
