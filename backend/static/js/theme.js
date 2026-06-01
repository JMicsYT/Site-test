(function () {
  var STORAGE_KEY = 'shoshop-theme';

  function getTheme() {
    try {
      return localStorage.getItem(STORAGE_KEY) || 'dark';
    } catch (e) {
      return 'dark';
    }
  }

  function setTheme(value) {
    value = value === 'light' ? 'light' : 'dark';
    try {
      localStorage.setItem(STORAGE_KEY, value);
    } catch (e) {}
    document.documentElement.setAttribute('data-theme', value);
    var meta = document.querySelector('meta[name="color-scheme"]');
    if (meta) meta.setAttribute('content', value);
  }

  function init() {
    setTheme(getTheme());

    var btn = document.querySelector('.theme-toggle');
    if (btn) {
      btn.addEventListener('click', function () {
        var next = getTheme() === 'dark' ? 'light' : 'dark';
        setTheme(next);
      });
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
