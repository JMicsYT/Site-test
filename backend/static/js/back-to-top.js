(function () {
  var btn = document.querySelector('.back-to-top');
  if (!btn) return;

  function onScroll() {
    if (window.scrollY > 400) {
      btn.classList.add('visible');
    } else {
      btn.classList.remove('visible');
    }
  }

  function goTop() {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  window.addEventListener('scroll', onScroll, { passive: true });
  btn.addEventListener('click', goTop);
})();
