// Small, dependency-free interactions for Foluso's portfolio.
document.querySelector('#year').textContent = new Date().getFullYear();

const filters = [...document.querySelectorAll('.filter')];
const cards = [...document.querySelectorAll('.project-card')];
filters.forEach((button) => button.addEventListener('click', () => {
  filters.forEach((item) => item.classList.toggle('active', item === button));
  const category = button.dataset.filter;
  cards.forEach((card) => card.classList.toggle('is-hidden', category !== 'all' && card.dataset.category !== category));
}));

const menuButton = document.querySelector('.menu-toggle');
const nav = document.querySelector('.topbar nav');
menuButton.addEventListener('click', () => {
  const open = menuButton.getAttribute('aria-expanded') !== 'true';
  menuButton.setAttribute('aria-expanded', String(open));
  nav.classList.toggle('open', open);
  menuButton.setAttribute('aria-label', open ? 'Close navigation' : 'Open navigation');
});
nav.querySelectorAll('a').forEach((link) => link.addEventListener('click', () => {
  nav.classList.remove('open');
  menuButton.setAttribute('aria-expanded', 'false');
  menuButton.setAttribute('aria-label', 'Open navigation');
}));

// Progressive reveal: content remains visible if IntersectionObserver is unavailable.
if ('IntersectionObserver' in window && !window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
  const observer = new IntersectionObserver((entries, currentObserver) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
        currentObserver.unobserve(entry.target);
      }
    });
  }, { threshold: 0.12 });
  document.querySelectorAll('.section-head, .project-card, .about-right, .service-list article, .manifesto blockquote').forEach((item) => {
    item.classList.add('reveal');
    observer.observe(item);
  });
}
