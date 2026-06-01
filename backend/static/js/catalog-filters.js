/* AJAX-обновление сетки каталога при изменении любого фильтра. */
(function () {
    'use strict';

    document.addEventListener('DOMContentLoaded', function () {
        var form = document.querySelector('[data-filters-form]');
        var container = document.querySelector('[data-grid-container]');
        var totalEl = document.querySelector('[data-total-count]');
        if (!form || !container) return;

        var debounceTimer = null;

        function scheduleUpdate() {
            if (debounceTimer) clearTimeout(debounceTimer);
            debounceTimer = setTimeout(applyFilters, 300);
        }

        form.addEventListener('change', scheduleUpdate);
        form.addEventListener('submit', function (e) {
            e.preventDefault();
            applyFilters();
        });

        // Инпуты цены/поиска — обновлять с debounce
        Array.prototype.forEach.call(
            form.querySelectorAll('input[type="search"], input[type="number"]'),
            function (el) { el.addEventListener('input', scheduleUpdate); }
        );

        function applyFilters() {
            var qs = new URLSearchParams(new FormData(form)).toString();
            container.classList.add('is-loading');
            fetch(window.location.pathname + '?' + qs, {
                headers: { 'X-Requested-With': 'XMLHttpRequest' },
                credentials: 'same-origin',
            })
                .then(function (r) { return r.ok ? r.text() : null; })
                .then(function (html) {
                    if (!html) return;
                    container.innerHTML = html;
                    // обновить URL без перезагрузки
                    var newUrl = window.location.pathname + (qs ? '?' + qs : '');
                    window.history.replaceState({}, '', newUrl);
                    // пересчитать счётчик из партиала (если есть)
                    var countAttr = container.querySelector('[data-count-hint]');
                    if (totalEl && countAttr) {
                        totalEl.textContent = countAttr.getAttribute('data-count-hint');
                    }
                })
                .catch(function () {})
                .finally(function () {
                    container.classList.remove('is-loading');
                });
        }
    });
})();
