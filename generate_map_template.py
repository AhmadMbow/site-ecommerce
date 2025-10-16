#!/usr/bin/env python3
"""Script pour générer le template map.html ultra-moderne et complet"""

template_content = """{% extends "livreur/base_livreur.html" %}

{% block title %}Carte Interactive - DashLivr{% endblock %}
{% block header %}Carte Interactive des Livraisons{% endblock %}

{% block extra_css %}
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
<link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.css" />
<link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.Default.css" />
<style>
:root {
  --gradient-primary: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  --gradient-pending: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  --gradient-progress: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
  --gradient-completed: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
  --shadow-sm: 0 2px 8px rgba(0,0,0,0.08);
  --shadow-md: 0 4px 16px rgba(0,0,0,0.12);
  --shadow-lg: 0 8px 24px rgba(0,0,0,0.15);
  --shadow-xl: 0 12px 32px rgba(0,0,0,0.18);
}

/* Main Container */
.map-page-container {
  display: grid;
  grid-template-columns: 350px 1fr;
  gap: 1.5rem;
  height: calc(100vh - 180px);
  min-height: 600px;
}

/* Left Sidebar */
.map-sidebar {
  background: white;
  border-radius: 16px;
  box-shadow: var(--shadow-sm);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.sidebar-header {
  background: var(--gradient-primary);
  color: white;
  padding: 1.5rem;
  position: relative;
  overflow: hidden;
}

.sidebar-header::before {
  content: '';
  position: absolute;
  top: -50%;
  right: -10%;
  width: 200px;
  height: 200px;
  background: rgba(255,255,255,0.1);
  border-radius: 50%;
}

.sidebar-title {
  font-size: 1.25rem;
  font-weight: 700;
  margin: 0 0 0.5rem 0;
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.sidebar-subtitle {
  font-size: 0.875rem;
  opacity: 0.9;
  margin: 0;
}

/* Stats Mini Cards */
.sidebar-stats {
  padding: 1rem;
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 0.75rem;
  border-bottom: 1px solid #f1f5f9;
}

.mini-stat {
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  padding: 1rem;
  border-radius: 12px;
  text-align: center;
  transition: all 0.3s;
  cursor: pointer;
  position: relative;
  overflow: hidden;
}

.mini-stat::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 3px;
}

.mini-stat:nth-child(1)::before {background: var(--gradient-pending);}
.mini-stat:nth-child(2)::before {background: var(--gradient-progress);}
.mini-stat:nth-child(3)::before {background: var(--gradient-completed);}
.mini-stat:nth-child(4)::before {background: var(--gradient-primary);}

.mini-stat:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.mini-stat-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: #1e293b;
  margin-bottom: 0.25rem;
}

.mini-stat-label {
  font-size: 0.75rem;
  color: #64748b;
  font-weight: 600;
  text-transform: uppercase;
}

/* Search & Filters */
.sidebar-filters {
  padding: 1rem;
  border-bottom: 1px solid #f1f5f9;
}

.search-box {
  position: relative;
  margin-bottom: 1rem;
}

.search-input {
  width: 100%;
  padding: 0.75rem 2.5rem 0.75rem 1rem;
  border: 2px solid #e2e8f0;
  border-radius: 10px;
  font-size: 0.875rem;
  transition: all 0.3s;
}

.search-input:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 4px rgba(102, 126, 234, 0.1);
}

.search-icon {
  position: absolute;
  right: 1rem;
  top: 50%;
  transform: translateY(-50%);
  color: #94a3b8;
  pointer-events: none;
}

.filter-section {
  margin-bottom: 1rem;
}

.filter-label {
  font-size: 0.75rem;
  font-weight: 700;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 0.5rem;
  display: block;
}

.filter-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.filter-chip {
  padding: 0.5rem 1rem;
  border: 2px solid #e2e8f0;
  border-radius: 8px;
  font-size: 0.8125rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
  background: white;
  color: #64748b;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.filter-chip:hover {
  border-color: #cbd5e1;
  transform: translateY(-1px);
}

.filter-chip.active {
  border-color: transparent;
  color: white;
}

.filter-chip.active.pending {background: var(--gradient-pending);}
.filter-chip.active.progress {background: var(--gradient-progress);}
.filter-chip.active.completed {background: var(--gradient-completed);}

.chip-count {
  background: rgba(0,0,0,0.1);
  padding: 0.125rem 0.5rem;
  border-radius: 6px;
  font-size: 0.75rem;
  font-weight: 700;
}

.filter-chip.active .chip-count {
  background: rgba(255,255,255,0.3);
}

/* Orders List */
.sidebar-orders {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
}

.order-item {
  background: white;
  border: 1px solid #f1f5f9;
  border-radius: 12px;
  padding: 1rem;
  margin-bottom: 0.75rem;
  cursor: pointer;
  transition: all 0.3s;
}

.order-item:hover {
  border-color: #667eea;
  box-shadow: var(--shadow-md);
  transform: translateX(4px);
}

.order-item.selected {
  border-color: #667eea;
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.05) 0%, rgba(118, 75, 162, 0.05) 100%);
  box-shadow: var(--shadow-md);
}

.order-header-mini {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.order-id-mini {
  font-weight: 700;
  color: #1e293b;
  font-size: 0.875rem;
}

.order-status-badge {
  padding: 0.25rem 0.625rem;
  border-radius: 6px;
  font-size: 0.6875rem;
  font-weight: 700;
  text-transform: uppercase;
}

.status-pending {background: #fef3c7; color: #92400e;}
.status-progress {background: #dbeafe; color: #1e40af;}
.status-completed {background: #d1fae5; color: #065f46;}

.order-customer {
  font-size: 0.8125rem;
  color: #64748b;
  margin-bottom: 0.375rem;
  display: flex;
  align-items: center;
  gap: 0.375rem;
}

.order-address {
  font-size: 0.75rem;
  color: #94a3b8;
  display: flex;
  align-items: center;
  gap: 0.375rem;
}

/* Map Container */
.map-container {
  position: relative;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: var(--shadow-lg);
  background: white;
}

#deliveryMap {
  width: 100%;
  height: 100%;
  min-height: 600px;
}

/* Map Controls Overlay */
.map-controls-overlay {
  position: absolute;
  top: 1rem;
  right: 1rem;
  z-index: 1000;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.control-btn {
  width: 44px;
  height: 44px;
  background: white;
  border: none;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.125rem;
  color: #64748b;
  cursor: pointer;
  transition: all 0.3s;
  box-shadow: var(--shadow-md);
}

.control-btn:hover {
  background: #667eea;
  color: white;
  transform: scale(1.1);
  box-shadow: var(--shadow-lg);
}

.control-btn.active {
  background: var(--gradient-primary);
  color: white;
}

/* Map Legend */
.map-legend {
  position: absolute;
  bottom: 1rem;
  left: 1rem;
  z-index: 1000;
  background: white;
  border-radius: 12px;
  padding: 1rem;
  box-shadow: var(--shadow-lg);
  min-width: 200px;
}

.legend-title {
  font-size: 0.875rem;
  font-weight: 700;
  color: #1e293b;
  margin-bottom: 0.75rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.legend-items {
  display: grid;
  gap: 0.5rem;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-size: 0.8125rem;
  color: #64748b;
}

.legend-marker {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  border: 2px solid white;
  box-shadow: 0 2px 4px rgba(0,0,0,0.3);
}

.marker-pending {background: #f59e0b;}
.marker-progress {background: #3b82f6;}
.marker-completed {background: #10b981;}
.marker-driver {background: #ef4444;}

/* Loading Overlay */
.map-loading {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255,255,255,0.95);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  flex-direction: column;
  gap: 1rem;
}

.loading-spinner {
  width: 50px;
  height: 50px;
  border: 4px solid #e2e8f0;
  border-top-color: #667eea;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.loading-text {
  font-size: 0.875rem;
  color: #64748b;
  font-weight: 600;
}

@keyframes spin {
  to {transform: rotate(360deg);}
}

/* Custom Popup */
.custom-popup {
  font-family: 'Inter', sans-serif;
  padding: 0.5rem;
}

.popup-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
  padding-bottom: 0.75rem;
  border-bottom: 1px solid #e2e8f0;
}

.popup-order-id {
  font-weight: 700;
  color: #1e293b;
  font-size: 1rem;
}

.popup-content {
  display: grid;
  gap: 0.5rem;
}

.popup-row {
  display: flex;
  align-items: flex-start;
  gap: 0.5rem;
  font-size: 0.8125rem;
}

.popup-icon {
  color: #667eea;
  font-size: 0.875rem;
  margin-top: 0.125rem;
}

.popup-label {
  color: #64748b;
  font-weight: 600;
  min-width: 70px;
}

.popup-value {
  color: #1e293b;
  font-weight: 500;
  flex: 1;
}

.popup-actions {
  display: flex;
  gap: 0.5rem;
  margin-top: 0.75rem;
  padding-top: 0.75rem;
  border-top: 1px solid #e2e8f0;
}

.popup-btn {
  flex: 1;
  padding: 0.5rem;
  border: none;
  border-radius: 6px;
  font-size: 0.75rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.375rem;
}

.popup-btn-primary {
  background: var(--gradient-primary);
  color: white;
}

.popup-btn-secondary {
  background: #f1f5f9;
  color: #64748b;
}

.popup-btn:hover {
  transform: translateY(-1px);
  box-shadow: var(--shadow-sm);
}

/* Responsive */
@media (max-width: 1024px) {
  .map-page-container {
    grid-template-columns: 300px 1fr;
    gap: 1rem;
  }
}

@media (max-width: 768px) {
  .map-page-container {
    grid-template-columns: 1fr;
    height: auto;
  }
  
  .map-sidebar {
    max-height: 400px;
    order: 2;
  }
  
  .map-container {
    order: 1;
    height: 500px;
  }
  
  .sidebar-stats {
    grid-template-columns: repeat(4, 1fr);
  }
  
  .map-controls-overlay {
    flex-direction: row;
    top: auto;
    bottom: 1rem;
    right: 1rem;
    left: 1rem;
    justify-content: flex-end;
  }
  
  .map-legend {
    left: 1rem;
    bottom: 5rem;
  }
}

/* Dark Mode Support */
[data-theme="dark"] .map-sidebar,
[data-theme="dark"] .map-container,
[data-theme="dark"] .control-btn,
[data-theme="dark"] .map-legend,
[data-theme="dark"] .order-item,
[data-theme="dark"] .map-loading {
  background: var(--bg-secondary);
  border-color: var(--border);
}

[data-theme="dark"] .search-input,
[data-theme="dark"] .filter-chip {
  background: var(--bg-primary);
  border-color: var(--border);
  color: var(--text-primary);
}

[data-theme="dark"] .mini-stat {
  background: var(--bg-primary);
}

[data-theme="dark"] .control-btn:hover {
  background: var(--gradient-primary);
}

/* Animations */
@keyframes fadeIn {
  from {opacity: 0;}
  to {opacity: 1;}
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.order-item {
  animation: slideUp 0.3s ease-out backwards;
}

.order-item:nth-child(1) {animation-delay: 0.05s;}
.order-item:nth-child(2) {animation-delay: 0.1s;}
.order-item:nth-child(3) {animation-delay: 0.15s;}
.order-item:nth-child(4) {animation-delay: 0.2s;}
.order-item:nth-child(5) {animation-delay: 0.25s;}
</style>
{% endblock %}

{% block content %}
<div class="map-page-container">
  <!-- Left Sidebar -->
  <div class="map-sidebar">
    <div class="sidebar-header">
      <h2 class="sidebar-title">
        <i class="fas fa-map-marked-alt"></i>
        Livraisons
      </h2>
      <p class="sidebar-subtitle">{{ orders.count }} commande{{ orders.count|pluralize }} à livrer</p>
    </div>
    
    <div class="sidebar-stats">
      <div class="mini-stat" data-filter="pending">
        <div class="mini-stat-value">{{ stats.pending }}</div>
        <div class="mini-stat-label">En attente</div>
      </div>
      <div class="mini-stat" data-filter="progress">
        <div class="mini-stat-value">{{ stats.in_progress }}</div>
        <div class="mini-stat-label">En cours</div>
      </div>
      <div class="mini-stat" data-filter="completed">
        <div class="mini-stat-value">{{ stats.completed }}</div>
        <div class="mini-stat-label">Livrées</div>
      </div>
      <div class="mini-stat" data-filter="all">
        <div class="mini-stat-value">{{ stats.count_all }}</div>
        <div class="mini-stat-label">Total</div>
      </div>
    </div>
    
    <div class="sidebar-filters">
      <div class="search-box">
        <input type="text" class="search-input" id="orderSearchMap" placeholder="Rechercher une commande...">
        <i class="fas fa-search search-icon"></i>
      </div>
      
      <div class="filter-section">
        <label class="filter-label">Filtrer par statut</label>
        <div class="filter-chips">
          <button class="filter-chip active pending" data-status="all">
            <i class="fas fa-border-all"></i>
            <span>Toutes</span>
            <span class="chip-count">{{ stats.count_all }}</span>
          </button>
          <button class="filter-chip pending" data-status="EN_ATTENTE">
            <i class="fas fa-clock"></i>
            <span>En attente</span>
            <span class="chip-count">{{ stats.pending }}</span>
          </button>
          <button class="filter-chip progress" data-status="EN_COURS">
            <i class="fas fa-truck"></i>
            <span>En cours</span>
            <span class="chip-count">{{ stats.in_progress }}</span>
          </button>
          <button class="filter-chip completed" data-status="LIVREE">
            <i class="fas fa-check"></i>
            <span>Livrées</span>
            <span class="chip-count">{{ stats.completed }}</span>
          </button>
        </div>
      </div>
    </div>
    
    <div class="sidebar-orders" id="ordersList">
      {% for order in orders %}
      <div class="order-item" data-order-id="{{ order.id }}" data-status="{{ order.statut }}" data-lat="{{ order.adresse.latitude|default:'' }}" data-lng="{{ order.adresse.longitude|default:'' }}" data-search="{{ order.id }} {{ order.user.get_full_name|default:order.user.username }}">
        <div class="order-header-mini">
          <span class="order-id-mini">#{{ order.id }}</span>
          <span class="order-status-badge status-{{ order.statut|lower|slice:':4' }}">
            {% if order.statut == 'EN_ATTENTE' %}En attente
            {% elif order.statut == 'EN_COURS' %}En cours
            {% elif order.statut == 'LIVREE' %}Livrée
            {% endif %}
          </span>
        </div>
        <div class="order-customer">
          <i class="fas fa-user"></i>
          {{ order.user.get_full_name|default:order.user.username }}
        </div>
        <div class="order-address">
          <i class="fas fa-map-marker-alt"></i>
          {% if order.adresse_gps %}
            {{ order.adresse_gps|truncatechars:40 }}
          {% else %}
            Adresse non définie
          {% endif %}
        </div>
      </div>
      {% empty %}
      <div style="text-align: center; padding: 2rem; color: #94a3b8;">
        <i class="fas fa-inbox" style="font-size: 3rem; margin-bottom: 1rem;"></i>
        <p>Aucune commande disponible</p>
      </div>
      {% endfor %}
    </div>
  </div>
  
  <!-- Map Container -->
  <div class="map-container">
    <div class="map-loading" id="mapLoading">
      <div class="loading-spinner"></div>
      <div class="loading-text">Chargement de la carte...</div>
    </div>
    
    <div id="deliveryMap"></div>
    
    <div class="map-controls-overlay">
      <button class="control-btn" id="locateBtn" title="Ma position">
        <i class="fas fa-crosshairs"></i>
      </button>
      <button class="control-btn" id="clusterBtn" title="Clustering">
        <i class="fas fa-layer-group"></i>
      </button>
      <button class="control-btn" id="fullscreenBtn" title="Plein écran">
        <i class="fas fa-expand"></i>
      </button>
      <button class="control-btn" id="refreshBtn" title="Actualiser">
        <i class="fas fa-sync-alt"></i>
      </button>
    </div>
    
    <div class="map-legend">
      <div class="legend-title">
        <i class="fas fa-info-circle"></i>
        Légende
      </div>
      <div class="legend-items">
        <div class="legend-item">
          <div class="legend-marker marker-pending"></div>
          <span>En attente</span>
        </div>
        <div class="legend-item">
          <div class="legend-marker marker-progress"></div>
          <span>En cours</span>
        </div>
        <div class="legend-item">
          <div class="legend-marker marker-completed"></div>
          <span>Livrées</span>
        </div>
        <div class="legend-item">
          <div class="legend-marker marker-driver"></div>
          <span>Ma position</span>
        </div>
      </div>
    </div>
  </div>
</div>
{% endblock %}

{% block extra_js %}
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script src="https://unpkg.com/leaflet.markercluster@1.5.3/dist/leaflet.markercluster.js"></script>
<script>
let map, markers = {}, markerClusterGroup, currentLocationMarker;
let clusteringEnabled = true;

// Initialize map
document.addEventListener('DOMContentLoaded', function() {
  initMap();
  initFilters();
  initSearch();
  initControls();
  
  console.log('✅ Map page initialized - Ultra modern design loaded');
});

function initMap() {
  // Center on Senegal
  const defaultCenter = [14.6928, -17.4467]; // Dakar
  const defaultZoom = 12;
  
  // Create map
  map = L.map('deliveryMap', {
    zoomControl: false
  }).setView(defaultCenter, defaultZoom);
  
  // Add zoom control to bottom right
  L.control.zoom({
    position: 'bottomright'
  }).addTo(map);
  
  // Add tile layer
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors',
    maxZoom: 19
  }).addTo(map);
  
  // Initialize marker cluster group
  markerClusterGroup = L.markerClusterGroup({
    maxClusterRadius: 80,
    spiderfyOnMaxZoom: true,
    showCoverageOnHover: false,
    zoomToBoundsOnClick: true
  });
  
  map.addLayer(markerClusterGroup);
  
  // Add orders to map
  addOrdersToMap();
  
  // Try to get user location
  getUserLocation();
  
  // Hide loading
  setTimeout(() => {
    document.getElementById('mapLoading').style.display = 'none';
  }, 1000);
  
  // Fit bounds if markers exist
  setTimeout(() => {
    if (Object.keys(markers).length > 0) {
      const bounds = markerClusterGroup.getBounds();
      if (bounds.isValid()) {
        map.fitBounds(bounds, {padding: [50, 50]});
      }
    }
  }, 1500);
}

function addOrdersToMap() {
  const orderItems = document.querySelectorAll('.order-item');
  
  orderItems.forEach(item => {
    const lat = parseFloat(item.dataset.lat);
    const lng = parseFloat(item.dataset.lng);
    const orderId = item.dataset.orderId;
    const status = item.dataset.status;
    
    if (lat && lng) {
      const markerColor = getMarkerColor(status);
      
      const customIcon = L.divIcon({
        className: 'custom-marker',
        html: `<div style="
          width: 32px;
          height: 32px;
          background: ${markerColor};
          border: 3px solid white;
          border-radius: 50%;
          box-shadow: 0 3px 10px rgba(0,0,0,0.3);
          display: flex;
          align-items: center;
          justify-content: center;
          color: white;
          font-weight: 700;
          font-size: 0.75rem;
        ">${orderId}</div>`,
        iconSize: [32, 32],
        iconAnchor: [16, 32]
      });
      
      const marker = L.marker([lat, lng], {icon: customIcon});
      
      // Create popup content
      const popupContent = createPopupContent(item);
      marker.bindPopup(popupContent, {
        maxWidth: 300,
        className: 'custom-popup'
      });
      
      // Add click event
      marker.on('click', () => {
        selectOrderItem(orderId);
      });
      
      markerClusterGroup.addLayer(marker);
      markers[orderId] = marker;
      
      // Add click event to order item
      item.addEventListener('click', () => {
        selectOrderItem(orderId);
        map.setView([lat, lng], 16);
        marker.openPopup();
      });
    }
  });
}

function getMarkerColor(status) {
  switch(status) {
    case 'EN_ATTENTE': return '#f59e0b';
    case 'EN_COURS': return '#3b82f6';
    case 'LIVREE': return '#10b981';
    default: return '#6b7280';
  }
}

function createPopupContent(orderItem) {
  const orderId = orderItem.dataset.orderId;
  const customerName = orderItem.querySelector('.order-customer').textContent.trim();
  const address = orderItem.querySelector('.order-address').textContent.trim();
  const status = orderItem.dataset.status;
  
  let statusText = status;
  let statusClass = '';
  if (status === 'EN_ATTENTE') {
    statusText = 'En attente';
    statusClass = 'status-pending';
  } else if (status === 'EN_COURS') {
    statusText = 'En cours';
    statusClass = 'status-progress';
  } else if (status === 'LIVREE') {
    statusText = 'Livrée';
    statusClass = 'status-completed';
  }
  
  return `
    <div class="popup-header">
      <span class="popup-order-id">Commande #${orderId}</span>
      <span class="order-status-badge ${statusClass}">${statusText}</span>
    </div>
    <div class="popup-content">
      <div class="popup-row">
        <i class="fas fa-user popup-icon"></i>
        <span class="popup-label">Client:</span>
        <span class="popup-value">${customerName}</span>
      </div>
      <div class="popup-row">
        <i class="fas fa-map-marker-alt popup-icon"></i>
        <span class="popup-label">Adresse:</span>
        <span class="popup-value">${address}</span>
      </div>
    </div>
    <div class="popup-actions">
      <a href="/livreur/orders/${orderId}/" class="popup-btn popup-btn-primary">
        <i class="fas fa-info-circle"></i>
        Détails
      </a>
      <button class="popup-btn popup-btn-secondary" onclick="openDirections(${orderItem.dataset.lat}, ${orderItem.dataset.lng})">
        <i class="fas fa-route"></i>
        Itinéraire
      </button>
    </div>
  `;
}

function selectOrderItem(orderId) {
  document.querySelectorAll('.order-item').forEach(item => {
    item.classList.remove('selected');
  });
  
  const selectedItem = document.querySelector(`[data-order-id="${orderId}"]`);
  if (selectedItem) {
    selectedItem.classList.add('selected');
    selectedItem.scrollIntoView({behavior: 'smooth', block: 'nearest'});
  }
}

function getUserLocation() {
  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(
      position => {
        const lat = position.coords.latitude;
        const lng = position.coords.longitude;
        
        if (currentLocationMarker) {
          map.removeLayer(currentLocationMarker);
        }
        
        const locationIcon = L.divIcon({
          className: 'current-location-marker',
          html: `<div style="
            width: 20px;
            height: 20px;
            background: #ef4444;
            border: 4px solid white;
            border-radius: 50%;
            box-shadow: 0 3px 10px rgba(239, 68, 68, 0.5);
            animation: pulse 2s infinite;
          "></div>`,
          iconSize: [20, 20],
          iconAnchor: [10, 10]
        });
        
        currentLocationMarker = L.marker([lat, lng], {icon: locationIcon})
          .addTo(map)
          .bindPopup('<b>Votre position actuelle</b>');
      },
      error => {
        console.log('Geolocation error:', error);
      }
    );
  }
}

function initFilters() {
  const filterChips = document.querySelectorAll('.filter-chip');
  const miniStats = document.querySelectorAll('.mini-stat');
  
  filterChips.forEach(chip => {
    chip.addEventListener('click', () => {
      const status = chip.dataset.status;
      
      // Update active state
      filterChips.forEach(c => c.classList.remove('active'));
      chip.classList.add('active');
      
      // Filter orders
      filterOrders(status);
    });
  });
  
  miniStats.forEach(stat => {
    stat.addEventListener('click', () => {
      const filter = stat.dataset.filter;
      const statusMap = {
        'pending': 'EN_ATTENTE',
        'progress': 'EN_COURS',
        'completed': 'LIVREE',
        'all': 'all'
      };
      
      const status = statusMap[filter];
      
      // Find and click corresponding filter chip
      const chip = document.querySelector(`[data-status="${status}"]`);
      if (chip) chip.click();
    });
  });
}

function filterOrders(status) {
  const orderItems = document.querySelectorAll('.order-item');
  markerClusterGroup.clearLayers();
  
  orderItems.forEach(item => {
    const itemStatus = item.dataset.status;
    
    if (status === 'all' || itemStatus === status) {
      item.style.display = 'block';
      
      // Re-add marker
      const orderId = item.dataset.orderId;
      if (markers[orderId]) {
        markerClusterGroup.addLayer(markers[orderId]);
      }
    } else {
      item.style.display = 'none';
    }
  });
  
  // Fit bounds to visible markers
  setTimeout(() => {
    const bounds = markerClusterGroup.getBounds();
    if (bounds.isValid()) {
      map.fitBounds(bounds, {padding: [50, 50]});
    }
  }, 100);
}

function initSearch() {
  const searchInput = document.getElementById('orderSearchMap');
  
  searchInput.addEventListener('input', () => {
    const searchTerm = searchInput.value.toLowerCase().trim();
    const orderItems = document.querySelectorAll('.order-item');
    
    orderItems.forEach(item => {
      const searchText = item.dataset.search.toLowerCase();
      
      if (searchText.includes(searchTerm)) {
        item.style.display = 'block';
      } else {
        item.style.display = 'none';
      }
    });
  });
}

function initControls() {
  // Locate button
  document.getElementById('locateBtn').addEventListener('click', () => {
    getUserLocation();
    if (currentLocationMarker) {
      map.setView(currentLocationMarker.getLatLng(), 15);
      currentLocationMarker.openPopup();
    }
  });
  
  // Cluster button
  document.getElementById('clusterBtn').addEventListener('click', function() {
    clusteringEnabled = !clusteringEnabled;
    this.classList.toggle('active');
    
    if (clusteringEnabled) {
      markerClusterGroup.clearLayers();
      Object.values(markers).forEach(marker => {
        markerClusterGroup.addLayer(marker);
      });
    } else {
      markerClusterGroup.clearLayers();
      Object.values(markers).forEach(marker => {
        marker.addTo(map);
      });
    }
  });
  
  // Fullscreen button
  document.getElementById('fullscreenBtn').addEventListener('click', function() {
    const mapContainer = document.querySelector('.map-container');
    
    if (!document.fullscreenElement) {
      mapContainer.requestFullscreen().catch(err => {
        console.log('Fullscreen error:', err);
      });
      this.innerHTML = '<i class="fas fa-compress"></i>';
    } else {
      document.exitFullscreen();
      this.innerHTML = '<i class="fas fa-expand"></i>';
    }
  });
  
  // Refresh button
  document.getElementById('refreshBtn').addEventListener('click', function() {
    this.style.animation = 'spin 0.5s linear';
    
    // Simulate refresh
    setTimeout(() => {
      location.reload();
    }, 500);
  });
}

function openDirections(lat, lng) {
  const url = `https://www.google.com/maps/dir/?api=1&destination=${lat},${lng}`;
  window.open(url, '_blank');
}

// Add pulse animation for current location
const style = document.createElement('style');
style.textContent = `
  @keyframes pulse {
    0% {
      box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7);
    }
    70% {
      box-shadow: 0 0 0 15px rgba(239, 68, 68, 0);
    }
    100% {
      box-shadow: 0 0 0 0 rgba(239, 68, 68, 0);
    }
  }
`;
document.head.appendChild(style);
</script>
{% endblock %}
"""

# Écrire le template
output_file = '/home/ahmadmbow/e-commerce/ecommerce/templates/livreur/map.html'
with open(output_file, 'w', encoding='utf-8') as f:
    f.write(template_content)

print(f"✅ Template map.html créé avec succès: {output_file}")
print(f"📏 Taille: {len(template_content)} caractères")
print(f"🗺️ Fonctionnalités: Sidebar + Filtres + Recherche + Clustering + Géolocalisation")
