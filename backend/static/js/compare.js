/* Сравнение товаров: AJAX-переключение через [data-compare-toggle] */
(function () {
    'use strict';

    function getCsrfToken() {
        var m = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
        return m ? decodeURIComponent(m[1]) : '';
    }

    function showToast(msg, type) {
        if (window.ShoShopToast) {
            window.ShoShopToast.show(msg, type || 'success');
        }
    }

    function updateHeaderCounter(count) {
        var el = document.querySelector('[data-compare-count]');
        if (!el) return;
        el.textContent = count > 0 ? String(count) : '';
        el.classList.toggle('is-empty', count <= 0);
    }

    function handle(btn) {
        var pid = btn.getAttribute('data-product-id');
        if (!pid) return;
        btn.disabled = true;
        fetch('/compare/toggle/' + pid + '/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCsrfToken(),
                'X-Requested-With': 'XMLHttpRequest',
                'Accept': 'application/json',
            },
            credentials: 'same-origin',
        })
            .then(function (r) { return r.ok ? r.json() : null; })
            .then(function (data) {
                if (!data || !data.ok) return;
                btn.classList.toggle('is-active', !!data.in_compare);
                btn.setAttribute('title', data.in_compare ? 'В сравнении' : 'Сравнить');
                updateHeaderCounter(data.count);
                if (data.overflow) {
                    showToast('Можно сравнивать до 4 товаров одновременно', 'warning');
                } else {
                    showToast(
                        data.in_compare ? 'Добавлено к сравнению' : 'Убрано из сравнения',
                        'info'
                    );
                }
            })
            .catch(function () {
                showToast('Ошибка сети', 'error');
            })
            .finally(function () {
                btn.disabled = false;
            });
    }

    document.addEventListener('click', function (e) {
        var btn = e.target.closest('[data-compare-toggle]');
        if (!btn) return;
        e.preventDefault();
        handle(btn);
    });
})();
