/* Избранное: AJAX-переключение через [data-fav-toggle] */
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
        var el = document.querySelector('[data-fav-count]');
        if (!el) return;
        el.textContent = count > 0 ? String(count) : '';
        el.classList.toggle('is-empty', count <= 0);
    }

    function handle(btn) {
        var pid = btn.getAttribute('data-product-id');
        if (!pid) return;
        btn.disabled = true;
        fetch('/favorites/toggle/' + pid + '/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCsrfToken(),
                'X-Requested-With': 'XMLHttpRequest',
                'Accept': 'application/json',
            },
            credentials: 'same-origin',
        })
            .then(function (r) {
                if (r.status === 302 || r.status === 401 || r.status === 403) {
                    window.location.href = '/accounts/login/?next=' + encodeURIComponent(window.location.pathname);
                    return null;
                }
                return r.json();
            })
            .then(function (data) {
                if (!data || !data.ok) return;
                btn.classList.toggle('is-active', !!data.in_favorites);
                btn.setAttribute('title', data.in_favorites ? 'В избранном' : 'В избранное');
                updateHeaderCounter(data.count);
                showToast(
                    data.in_favorites ? 'Добавлено в избранное' : 'Удалено из избранного',
                    data.in_favorites ? 'success' : 'info'
                );
            })
            .catch(function () {
                showToast('Ошибка сети', 'error');
            })
            .finally(function () {
                btn.disabled = false;
            });
    }

    document.addEventListener('click', function (e) {
        var btn = e.target.closest('[data-fav-toggle]');
        if (!btn) return;
        e.preventDefault();
        handle(btn);
    });
})();
