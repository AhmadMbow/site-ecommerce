document.addEventListener('DOMContentLoaded', function() {
    // Initialize Bootstrap toasts
    var toastElList = [].slice.call(document.querySelectorAll('.toast'));
    var toastList = toastElList.map(function(toastEl) {
        return new bootstrap.Toast(toastEl);
    });
});

(function () {
  // CSRF depuis le cookie
  function getCookie(name) {
    const v = `; ${document.cookie || ''}`;
    const p = v.split(`; ${name}=`);
    if (p.length === 2) return decodeURIComponent(p.pop().split(';').shift());
  }
  const csrftoken = getCookie('csrftoken') || '';

  // Badge
  function badgeEls() { return document.querySelectorAll('#cart-count, .cart-count, #cartBadge'); }
  function updateCartBadge(count) {
    const n = Number(count) || 0;
    badgeEls().forEach(el => {
      el.textContent = n;
      el.style.display = n > 0 ? 'inline' : 'none';
      el.setAttribute('aria-label', `Articles au panier: ${n}`);
    });
  }
  async function refreshCartCount() {
    try {
      const res = await fetch('/cart-count/', {
        headers: { 'X-Requested-With': 'XMLHttpRequest' },
        credentials: 'same-origin'
      });
      const data = await res.json();
      updateCartBadge(data.count || 0);
    } catch (_) {}
  }

  // Toast Bootstrap (optionnel si présent dans le DOM)
  function showToast(msg) {
    const toastEl = document.querySelector('.toast');
    if (!toastEl) return;
    const body = toastEl.querySelector('.toast-body');
    if (body) body.textContent = msg || 'Ajouté au panier';
    const T = window.bootstrap && window.bootstrap.Toast;
    if (T) new T(toastEl).show();
  }

  // POST d’ajout
  async function addToCart(url) {
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'X-CSRFToken': csrftoken, 'X-Requested-With': 'XMLHttpRequest' },
      credentials: 'same-origin'
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    updateCartBadge(data.cart_count ?? data.count ?? 0);
    showToast(data.message || 'Produit ajouté');
  }

  // Delegation clic sur .js-add-to-cart
  document.addEventListener('click', (e) => {
    const btn = e.target.closest('.js-add-to-cart');
    if (!btn) return;
    const url = btn.getAttribute('data-url');
    if (!url) return;
    e.preventDefault();
    addToCart(url).catch(() => refreshCartCount());
  });

  // Init badge au chargement
  document.addEventListener('DOMContentLoaded', refreshCartCount);
})();

console.log('Fichier index.js chargé');

function initNotation() {
    document.querySelectorAll('.rating').forEach(container => {
        const stars = container.querySelectorAll('.star');
        const produitId = container.dataset.produitId;
        const input = container.querySelector('input[type="hidden"]');

        stars.forEach((star, index) => {
            star.addEventListener('mouseover', () => {
                for(let i = 0; i <= index; i++) {
                    stars[i].classList.add('hover');
                }
            });

            star.addEventListener('mouseout', () => {
                stars.forEach(s => s.classList.remove('hover'));
            });

            star.addEventListener('click', () => {
                const note = index + 1;
                noterProduit(produitId, note, container);
            });
        });
    });
}

function noterProduit(produitId, note, container) {
  const csrfEl = document.querySelector('[name=csrfmiddlewaretoken]');
  const csrftoken = csrfEl ? csrfEl.value : '';

  fetch(`/produit/${produitId}/noter/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrftoken,
            'Content-Type': 'application/x-www-form-urlencoded',
      'X-Requested-With': 'XMLHttpRequest',
        },
    body: `note=${encodeURIComponent(note)}`
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            updateStars(container, data.note_moyenne);
            showToast('Note enregistrée avec succès !');
      // Mettre à jour le compteur d'avis si présent
      const countSpan = container.querySelector('span');
      if (countSpan && data.nombre_notes != null) {
        countSpan.textContent = `(${data.nombre_notes} avis)`;
      }
        } else {
            showToast(data.error, 'danger');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('Une erreur est survenue', 'danger');
    });
}

function updateStars(container, note) {
    const stars = container.querySelectorAll('.star');
    stars.forEach((star, index) => {
        if (index < Math.floor(note)) {
            star.className = 'star fas fa-star text-warning';
        } else if (index < note) {
            star.className = 'star fas fa-star-half-alt text-warning';
        } else {
            star.className = 'star far fa-star text-warning';
        }
    });
}

document.addEventListener('DOMContentLoaded', initNotation);