#!/usr/bin/env python3
"""Script pour générer le template orders.html ultra-moderne"""

template_content = """{% extends "livreur/base_livreur.html" %}

{% block title %}Gestion des Commandes - DashLivr{% endblock %}
{% block header %}Gestion des Commandes{% endblock %}

{% block content %}
<!-- Hero Stats Banner -->
<div class="stats-banner">
  <div class="stat-card stat-all">
    <div class="stat-icon"><i class="fas fa-boxes"></i></div>
    <div class="stat-content">
      <div class="stat-label">Total</div>
      <div class="stat-value">{{ stats.count_all }}</div>
    </div>
  </div>
  
  <div class="stat-card stat-pending">
    <div class="stat-icon"><i class="fas fa-clock"></i></div>
    <div class="stat-content">
      <div class="stat-label">En Attente</div>
      <div class="stat-value">{{ stats.pending }}</div>
    </div>
  </div>
  
  <div class="stat-card stat-progress">
    <div class="stat-icon"><i class="fas fa-shipping-fast"></i></div>
    <div class="stat-content">
      <div class="stat-label">En Cours</div>
      <div class="stat-value">{{ stats.in_progress }}</div>
    </div>
  </div>
  
  <div class="stat-card stat-completed">
    <div class="stat-icon"><i class="fas fa-check-circle"></i></div>
    <div class="stat-content">
      <div class="stat-label">Livrées</div>
      <div class="stat-value">{{ stats.completed }}</div>
    </div>
  </div>
</div>

<!-- Advanced Filters & Search -->
<div class="filters-section">
  <div class="search-bar">
    <i class="fas fa-search search-icon"></i>
    <input type="text" id="orderSearch" placeholder="Rechercher par numéro, client, adresse..." class="search-input">
    <button class="search-clear" id="clearSearch" style="display: none;"><i class="fas fa-times"></i></button>
  </div>
  
  <div class="filter-pills">
    <a href="{% url 'livreur_orders' %}" class="filter-pill {% if not status_filter %}active{% endif %}">
      <i class="fas fa-border-all"></i><span>Toutes</span><span class="pill-badge">{{ stats.count_all }}</span>
    </a>
    <a href="{% url 'livreur_orders' %}?status=EN_ATTENTE" class="filter-pill filter-pending {% if status_filter == 'EN_ATTENTE' %}active{% endif %}">
      <i class="fas fa-hourglass-half"></i><span>En attente</span><span class="pill-badge">{{ stats.pending }}</span>
    </a>
    <a href="{% url 'livreur_orders' %}?status=EN_COURS" class="filter-pill filter-progress {% if status_filter == 'EN_COURS' %}active{% endif %}">
      <i class="fas fa-truck"></i><span>En cours</span><span class="pill-badge">{{ stats.in_progress }}</span>
    </a>
    <a href="{% url 'livreur_orders' %}?status=LIVREE" class="filter-pill filter-completed {% if status_filter == 'LIVREE' %}active{% endif %}">
      <i class="fas fa-check-double"></i><span>Livrées</span><span class="pill-badge">{{ stats.completed }}</span>
    </a>
  </div>
  
  <div class="view-toggle">
    <button class="view-btn active" data-view="grid" title="Vue grille"><i class="fas fa-th"></i></button>
    <button class="view-btn" data-view="list" title="Vue liste"><i class="fas fa-list"></i></button>
  </div>
</div>

<!-- Orders Grid -->
<div class="orders-container" id="ordersContainer">
  {% for order in orders %}
  <div class="order-card-modern" data-order-id="{{ order.id }}" data-status="{{ order.statut|lower }}" data-search-text="{{ order.id }} {{ order.user.get_full_name|default:order.user.username }} {{ order.adresse_gps|default:'' }}">
    
    <div class="card-header-modern">
      <div class="order-number"><i class="fas fa-hashtag"></i><span>{{ order.id }}</span></div>
      <div class="status-badge status-{{ order.statut|lower }}">
        {% if order.statut == 'EN_ATTENTE' %}<i class="fas fa-clock"></i> En attente
        {% elif order.statut == 'EN_COURS' %}<i class="fas fa-shipping-fast"></i> En cours
        {% elif order.statut == 'LIVREE' %}<i class="fas fa-check-circle"></i> Livrée
        {% else %}{{ order.get_statut_display|default:order.statut }}{% endif %}
      </div>
    </div>
    
    <div class="customer-section">
      <div class="customer-avatar">
        {% if order.user.userprofile and order.user.userprofile.profile_pic %}
          <img src="{{ order.user.userprofile.profile_pic.url }}" alt="{{ order.user.get_full_name }}">
        {% else %}<i class="fas fa-user"></i>{% endif %}
      </div>
      <div class="customer-info">
        <div class="customer-name">{{ order.user.get_full_name|default:order.user.username }}</div>
        <div class="customer-meta">
          <i class="far fa-calendar"></i><span>{{ order.date_commande|date:"d/m/Y" }}</span>
          <i class="far fa-clock"></i><span>{{ order.date_commande|date:"H:i" }}</span>
        </div>
      </div>
    </div>
    
    <div class="details-grid">
      <div class="detail-item">
        <div class="detail-icon"><i class="fas fa-coins"></i></div>
        <div class="detail-content">
          <div class="detail-label">Montant total</div>
          <div class="detail-value">{{ order.total|default:0|floatformat:0 }} FCFA</div>
        </div>
      </div>
      
      {% if order.adresse_gps %}
      <div class="detail-item">
        <div class="detail-icon"><i class="fas fa-map-marker-alt"></i></div>
        <div class="detail-content">
          <div class="detail-label">Position GPS</div>
          <div class="detail-value">{{ order.adresse_gps|truncatechars:30 }}</div>
        </div>
      </div>
      {% elif order.user.userprofile and order.user.userprofile.address %}
      <div class="detail-item">
        <div class="detail-icon"><i class="fas fa-home"></i></div>
        <div class="detail-content">
          <div class="detail-label">Adresse</div>
          <div class="detail-value">{{ order.user.userprofile.address|truncatechars:30 }}</div>
        </div>
      </div>
      {% endif %}
    </div>
    
    <div class="actions-bar">
      {% if order.statut == 'EN_ATTENTE' %}
        <form method="post" action="{% url 'livreur_order_update_status' order.id %}" class="action-form">
          {% csrf_token %}
          <input type="hidden" name="action" value="accept">
          <input type="hidden" name="next" value="{{ request.get_full_path }}">
          <button class="action-btn action-accept" type="submit">
            <i class="fas fa-play"></i><span>Accepter</span>
          </button>
        </form>
      {% elif order.statut == 'EN_COURS' %}
        <form method="post" action="{% url 'livreur_order_update_status' order.id %}" class="action-form">
          {% csrf_token %}
          <input type="hidden" name="action" value="complete">
          <input type="hidden" name="next" value="{{ request.get_full_path }}">
          <button class="action-btn action-complete" type="submit" onclick="return confirm('Confirmer la livraison ?')">
            <i class="fas fa-check"></i><span>Marquer livrée</span>
          </button>
        </form>
      {% elif order.statut == 'LIVREE' %}
        <div class="action-btn action-delivered disabled">
          <i class="fas fa-check-double"></i><span>Livraison terminée</span>
        </div>
      {% endif %}
      
      <a href="{% url 'livreur_order_detail' order.id %}" class="action-btn action-details">
        <i class="fas fa-info-circle"></i><span>Détails</span>
      </a>
      
      {% if order.adresse and order.adresse.latitude and order.adresse.longitude %}
        <a href="https://www.google.com/maps/dir/?api=1&destination={{ order.adresse.latitude }},{{ order.adresse.longitude }}" 
           target="_blank" class="action-btn action-map">
          <i class="fas fa-route"></i><span>Itinéraire</span>
        </a>
      {% endif %}
    </div>
    
    <div class="progress-indicator">
      <div class="progress-bar progress-{{ order.statut|lower }}"></div>
    </div>
  </div>
  {% empty %}
  <div class="empty-state">
    <div class="empty-icon"><i class="fas fa-box-open"></i></div>
    <h3 class="empty-title">Aucune commande trouvée</h3>
    <p class="empty-message">
      {% if status_filter %}Aucune commande avec le statut "{{ status_filter }}"
      {% else %}Aucune commande disponible pour le moment{% endif %}
    </p>
  </div>
  {% endfor %}
</div>

{% endblock %}

{% block extra_css %}
<style>
:root {
  --gradient-all: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  --gradient-pending: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  --gradient-progress: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
  --gradient-completed: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
  --shadow-sm: 0 2px 8px rgba(0,0,0,0.08);
  --shadow-md: 0 4px 16px rgba(0,0,0,0.12);
  --shadow-lg: 0 8px 24px rgba(0,0,0,0.15);
  --shadow-xl: 0 12px 32px rgba(0,0,0,0.18);
}
.stats-banner {display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 1.5rem; margin-bottom: 2rem;}
.stat-card {background: white; border-radius: 16px; padding: 1.5rem; display: flex; align-items: center; gap: 1.25rem; box-shadow: var(--shadow-sm); transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); position: relative; overflow: hidden;}
.stat-card::before {content: ''; position: absolute; top: 0; left: 0; width: 100%; height: 100%; opacity: 0.1; transition: opacity 0.3s;}
.stat-card:hover {transform: translateY(-4px); box-shadow: var(--shadow-lg);}
.stat-card:hover::before {opacity: 0.15;}
.stat-all::before {background: var(--gradient-all);}
.stat-pending::before {background: var(--gradient-pending);}
.stat-progress::before {background: var(--gradient-progress);}
.stat-completed::before {background: var(--gradient-completed);}
.stat-icon {width: 64px; height: 64px; border-radius: 14px; display: flex; align-items: center; justify-content: center; font-size: 1.75rem; color: white; flex-shrink: 0;}
.stat-all .stat-icon {background: var(--gradient-all);}
.stat-pending .stat-icon {background: var(--gradient-pending);}
.stat-progress .stat-icon {background: var(--gradient-progress);}
.stat-completed .stat-icon {background: var(--gradient-completed);}
.stat-content {flex: 1;}
.stat-label {font-size: 0.875rem; color: #64748b; font-weight: 500; margin-bottom: 0.25rem;}
.stat-value {font-size: 2rem; font-weight: 700; background: var(--gradient-all); -webkit-background-clip: text; -webkit-text-fill-color: transparent;}
.stat-pending .stat-value {background: var(--gradient-pending); -webkit-background-clip: text; -webkit-text-fill-color: transparent;}
.stat-progress .stat-value {background: var(--gradient-progress); -webkit-background-clip: text; -webkit-text-fill-color: transparent;}
.stat-completed .stat-value {background: var(--gradient-completed); -webkit-background-clip: text; -webkit-text-fill-color: transparent;}
.filters-section {background: white; border-radius: 16px; padding: 1.5rem; margin-bottom: 2rem; box-shadow: var(--shadow-sm); display: flex; flex-wrap: wrap; gap: 1rem; align-items: center;}
.search-bar {flex: 1; min-width: 280px; position: relative; display: flex; align-items: center;}
.search-icon {position: absolute; left: 1rem; color: #94a3b8; font-size: 1rem; pointer-events: none; z-index: 1;}
.search-input {width: 100%; padding: 0.875rem 3rem 0.875rem 2.75rem; border: 2px solid #e2e8f0; border-radius: 12px; font-size: 0.9375rem; transition: all 0.3s; background: #f8fafc;}
.search-input:focus {outline: none; border-color: #667eea; background: white; box-shadow: 0 0 0 4px rgba(102, 126, 234, 0.1);}
.search-clear {position: absolute; right: 0.75rem; background: #e2e8f0; border: none; border-radius: 8px; width: 32px; height: 32px; display: flex; align-items: center; justify-content: center; cursor: pointer; transition: all 0.2s; color: #64748b;}
.search-clear:hover {background: #cbd5e1; color: #334155;}
.filter-pills {display: flex; gap: 0.75rem; flex-wrap: wrap;}
.filter-pill {display: flex; align-items: center; gap: 0.5rem; padding: 0.75rem 1.25rem; border-radius: 12px; font-size: 0.875rem; font-weight: 600; border: 2px solid #e2e8f0; background: white; color: #64748b; text-decoration: none; transition: all 0.3s; cursor: pointer;}
.filter-pill:hover {border-color: #cbd5e1; transform: translateY(-2px); box-shadow: var(--shadow-sm);}
.filter-pill.active {background: var(--gradient-all); border-color: transparent; color: white; box-shadow: var(--shadow-md);}
.filter-pill.filter-pending.active {background: var(--gradient-pending);}
.filter-pill.filter-progress.active {background: var(--gradient-progress);}
.filter-pill.filter-completed.active {background: var(--gradient-completed);}
.pill-badge {background: rgba(255,255,255,0.2); padding: 0.25rem 0.5rem; border-radius: 8px; font-size: 0.75rem; font-weight: 700;}
.filter-pill.active .pill-badge {background: rgba(255,255,255,0.3);}
.view-toggle {display: flex; gap: 0.5rem; background: #f1f5f9; padding: 0.375rem; border-radius: 12px;}
.view-btn {background: transparent; border: none; padding: 0.625rem 1rem; border-radius: 8px; cursor: pointer; transition: all 0.2s; color: #64748b; font-size: 1rem;}
.view-btn:hover {color: #334155;}
.view-btn.active {background: white; color: #667eea; box-shadow: 0 2px 4px rgba(0,0,0,0.08);}
.orders-container {display: grid; grid-template-columns: repeat(auto-fill, minmax(380px, 1fr)); gap: 1.5rem;}
.orders-container.list-view {grid-template-columns: 1fr;}
.order-card-modern {background: white; border-radius: 16px; overflow: hidden; box-shadow: var(--shadow-sm); transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); border: 1px solid #f1f5f9;}
.order-card-modern:hover {transform: translateY(-6px); box-shadow: var(--shadow-xl); border-color: #e2e8f0;}
.card-header-modern {display: flex; justify-content: space-between; align-items: center; padding: 1.25rem 1.5rem; background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%); border-bottom: 1px solid #e2e8f0;}
.order-number {display: flex; align-items: center; gap: 0.5rem; font-size: 1.125rem; font-weight: 700; color: #334155;}
.order-number i {color: #94a3b8; font-size: 1rem;}
.status-badge {display: flex; align-items: center; gap: 0.5rem; padding: 0.5rem 1rem; border-radius: 10px; font-size: 0.8125rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.03em;}
.status-en_attente {background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%); color: #92400e; box-shadow: 0 2px 8px rgba(245, 158, 11, 0.2);}
.status-en_cours {background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%); color: #1e40af; box-shadow: 0 2px 8px rgba(59, 130, 246, 0.2);}
.status-livree {background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%); color: #065f46; box-shadow: 0 2px 8px rgba(16, 185, 129, 0.2);}
.customer-section {padding: 1.5rem; display: flex; align-items: center; gap: 1rem; border-bottom: 1px solid #f1f5f9;}
.customer-avatar {width: 56px; height: 56px; border-radius: 14px; background: var(--gradient-all); display: flex; align-items: center; justify-content: center; color: white; font-size: 1.5rem; flex-shrink: 0; overflow: hidden; box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);}
.customer-avatar img {width: 100%; height: 100%; object-fit: cover;}
.customer-info {flex: 1; min-width: 0;}
.customer-name {font-size: 1.0625rem; font-weight: 600; color: #1e293b; margin-bottom: 0.375rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;}
.customer-meta {display: flex; align-items: center; gap: 0.75rem; font-size: 0.8125rem; color: #64748b;}
.customer-meta i {color: #94a3b8;}
.details-grid {padding: 1.5rem; display: grid; gap: 1rem; background: #fafbfc;}
.detail-item {display: flex; align-items: flex-start; gap: 1rem; background: white; padding: 1rem; border-radius: 12px; border: 1px solid #f1f5f9; transition: all 0.2s;}
.detail-item:hover {border-color: #e2e8f0; box-shadow: 0 2px 8px rgba(0,0,0,0.05);}
.detail-icon {width: 40px; height: 40px; border-radius: 10px; background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%); display: flex; align-items: center; justify-content: center; color: #667eea; font-size: 1.125rem; flex-shrink: 0;}
.detail-content {flex: 1; min-width: 0;}
.detail-label {font-size: 0.8125rem; color: #64748b; font-weight: 500; margin-bottom: 0.25rem;}
.detail-value {font-size: 0.9375rem; font-weight: 600; color: #1e293b; word-wrap: break-word;}
.actions-bar {padding: 1.25rem; display: flex; flex-wrap: wrap; gap: 0.75rem; background: white; border-top: 1px solid #f1f5f9;}
.action-form {flex: 1; min-width: 140px; margin: 0;}
.action-btn {display: flex; align-items: center; justify-content: center; gap: 0.5rem; padding: 0.875rem 1.25rem; border-radius: 10px; font-size: 0.875rem; font-weight: 600; border: none; cursor: pointer; transition: all 0.3s; text-decoration: none; white-space: nowrap; width: 100%;}
.action-accept {background: var(--gradient-progress); color: white; box-shadow: 0 4px 12px rgba(79, 172, 254, 0.3);}
.action-accept:hover {transform: translateY(-2px); box-shadow: 0 6px 16px rgba(79, 172, 254, 0.4);}
.action-complete {background: var(--gradient-completed); color: white; box-shadow: 0 4px 12px rgba(67, 233, 123, 0.3);}
.action-complete:hover {transform: translateY(-2px); box-shadow: 0 6px 16px rgba(67, 233, 123, 0.4);}
.action-delivered {background: linear-gradient(135deg, #e2e8f0 0%, #cbd5e1 100%); color: #475569; cursor: not-allowed; opacity: 0.7;}
.action-details {background: white; color: #667eea; border: 2px solid #667eea; flex: 1; min-width: 120px;}
.action-details:hover {background: #667eea; color: white; transform: translateY(-2px); box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);}
.action-map {background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); color: white; flex: 1; min-width: 120px; box-shadow: 0 4px 12px rgba(240, 147, 251, 0.3);}
.action-map:hover {transform: translateY(-2px); box-shadow: 0 6px 16px rgba(240, 147, 251, 0.4);}
.progress-indicator {height: 4px; background: #f1f5f9; overflow: hidden;}
.progress-bar {height: 100%; transition: width 0.5s cubic-bezier(0.4, 0, 0.2, 1);}
.progress-en_attente .progress-bar {width: 33%; background: var(--gradient-pending);}
.progress-en_cours .progress-bar {width: 66%; background: var(--gradient-progress);}
.progress-livree .progress-bar {width: 100%; background: var(--gradient-completed);}
.empty-state {grid-column: 1 / -1; text-align: center; padding: 4rem 2rem; background: white; border-radius: 16px; box-shadow: var(--shadow-sm);}
.empty-icon {width: 120px; height: 120px; margin: 0 auto 1.5rem; background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%); border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 3.5rem; color: #94a3b8;}
.empty-title {font-size: 1.5rem; font-weight: 700; color: #334155; margin-bottom: 0.75rem;}
.empty-message {font-size: 1rem; color: #64748b; margin: 0;}
@keyframes fadeInUp {from {opacity: 0; transform: translateY(20px);} to {opacity: 1; transform: translateY(0);}}
.order-card-modern {animation: fadeInUp 0.4s ease-out;}
@media (max-width: 1024px) {
  .orders-container {grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 1.25rem;}
  .stats-banner {grid-template-columns: repeat(2, 1fr); gap: 1rem;}
}
@media (max-width: 768px) {
  .stats-banner {grid-template-columns: 1fr; gap: 1rem;}
  .stat-card {padding: 1.25rem;}
  .stat-icon {width: 52px; height: 52px; font-size: 1.5rem;}
  .stat-value {font-size: 1.75rem;}
  .filters-section {padding: 1rem; flex-direction: column; align-items: stretch;}
  .search-bar {width: 100%; min-width: auto;}
  .filter-pills {width: 100%; overflow-x: auto; flex-wrap: nowrap; padding-bottom: 0.5rem;}
  .filter-pill {flex-shrink: 0;}
  .view-toggle {width: 100%; justify-content: center;}
  .orders-container {grid-template-columns: 1fr; gap: 1rem;}
  .actions-bar {flex-direction: column;}
  .action-btn {width: 100%;}
  .action-form {width: 100%;}
}
@media (max-width: 480px) {
  .card-header-modern {flex-direction: column; align-items: flex-start; gap: 0.75rem;}
  .customer-section {padding: 1rem;}
  .customer-avatar {width: 48px; height: 48px; font-size: 1.25rem;}
  .details-grid {padding: 1rem;}
}
</style>
{% endblock %}

{% block extra_js %}
<script>
document.addEventListener('DOMContentLoaded', function() {
  const searchInput = document.getElementById('orderSearch');
  const clearBtn = document.getElementById('clearSearch');
  const orderCards = document.querySelectorAll('.order-card-modern');
  
  if (searchInput) {
    searchInput.addEventListener('input', function() {
      const searchTerm = this.value.toLowerCase().trim();
      clearBtn.style.display = searchTerm ? 'flex' : 'none';
      
      orderCards.forEach(card => {
        const searchText = card.dataset.searchText.toLowerCase();
        card.style.display = searchText.includes(searchTerm) ? '' : 'none';
      });
    });
    
    if (clearBtn) {
      clearBtn.addEventListener('click', function() {
        searchInput.value = '';
        searchInput.dispatchEvent(new Event('input'));
        searchInput.focus();
      });
    }
  }
  
  const viewBtns = document.querySelectorAll('.view-btn');
  const ordersContainer = document.getElementById('ordersContainer');
  
  viewBtns.forEach(btn => {
    btn.addEventListener('click', function() {
      viewBtns.forEach(b => b.classList.remove('active'));
      this.classList.add('active');
      
      if (this.dataset.view === 'list') {
        ordersContainer.classList.add('list-view');
      } else {
        ordersContainer.classList.remove('list-view');
      }
      
      localStorage.setItem('ordersView', this.dataset.view);
    });
  });
  
  const savedView = localStorage.getItem('ordersView');
  if (savedView === 'list') {
    document.querySelector('[data-view="list"]').click();
  }
  
  document.addEventListener('keydown', function(e) {
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
      e.preventDefault();
      searchInput.focus();
    }
    
    if (e.key === 'Escape' && searchInput === document.activeElement) {
      searchInput.value = '';
      searchInput.dispatchEvent(new Event('input'));
      searchInput.blur();
    }
  });
  
  console.log('✅ Orders page initialized - Ultra modern design loaded');
});
</script>
{% endblock %}
"""

# Écrire le template
output_file = '/home/ahmadmbow/e-commerce/ecommerce/templates/livreur/orders.html'
with open(output_file, 'w', encoding='utf-8') as f:
    f.write(template_content)

print(f"✅ Template créé avec succès: {output_file}")
print(f"📏 Taille: {len(template_content)} caractères")
