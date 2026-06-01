/* Универсальная toast-система.
   window.ShoShopToast.show(message, type='success', { duration=3500 }) */
(function () {
    'use strict';

    function ensureContainer() {
        var root = document.getElementById('toast-root');
        if (!root) {
            root = document.createElement('div');
            root.id = 'toast-root';
            root.className = 'toast-root';
            document.body.appendChild(root);
        }
        return root;
    }

    function show(message, type, opts) {
        var root = ensureContainer();
        var el = document.createElement('div');
        el.className = 'toast toast--' + (type || 'success');
        el.setAttribute('role', 'status');
        el.innerHTML = '<span class="toast__text"></span><button type="button" class="toast__close" aria-label="Закрыть">&times;</button>';
        el.querySelector('.toast__text').textContent = String(message);
        root.appendChild(el);
        requestAnimationFrame(function () { el.classList.add('is-visible'); });
        var duration = (opts && opts.duration) || 3500;
        var to = setTimeout(dismiss, duration);
        el.querySelector('.toast__close').addEventListener('click', dismiss);
        function dismiss() {
            clearTimeout(to);
            el.classList.remove('is-visible');
            el.classList.add('is-leaving');
            setTimeout(function () { el.remove(); }, 250);
        }
        return { dismiss: dismiss };
    }

    window.ShoShopToast = { show: show };
})();
