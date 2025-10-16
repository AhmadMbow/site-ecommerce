class DeliveryDashboard {
    constructor() {
        this.currentSection = 'dashboard';
        this.currentFilter = 'all';
        this.theme = localStorage.getItem('theme') || 'light';
        this.sampleOrders = [
            {
                id: 'SN001',
                customer: 'Awa Ndiaye',
                address: '10 Avenue Cheikh Anta Diop, Dakar',
                items: 3,
                amount: 15500,
                status: 'pending',
                time: '14:30',
                phone: '77 123 45 67'
            },
            {
                id: 'SN002',
                customer: 'Moussa Diop',
                address: 'Rue 6, Médina, Dakar',
                items: 2,
                amount: 9000,
                status: 'in-progress',
                time: '15:00',
                phone: '76 234 56 78'
            },
            {
                id: 'SN003',
                customer: 'Fatou Sarr',
                address: 'Cité Keur Gorgui, Dakar',
                items: 1,
                amount: 4500,
                status: 'completed',
                time: '13:45',
                phone: '78 345 67 89'
            },
            {
                id: 'SN004',
                customer: 'Ibrahima Fall',
                address: 'Liberté 6, Dakar',
                items: 4,
                amount: 21000,
                status: 'pending',
                time: '15:30',
                phone: '70 456 78 90'
            },
            {
                id: 'SN005',
                customer: 'Mariama Ba',
                address: 'Plateau, Dakar',
                items: 2,
                amount: 8000,
                status: 'in-progress',
                time: '16:00',
                phone: '75 567 89 01'
            }
        ];
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.initializeTheme();
        this.loadRecentOrders();
        this.loadOrders();
        this.updateNotificationCount();
    }

    setupEventListeners() {
        // Navigation latérale
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const section = e.currentTarget.dataset.section;
                this.showSection(section);
            });
        });

    // Menu mobile
        const mobileMenuBtn = document.getElementById('mobileMenuBtn');
        const sidebar = document.getElementById('sidebar');
        
        if (mobileMenuBtn) {
            mobileMenuBtn.addEventListener('click', () => {
                sidebar.classList.toggle('open');
            });
        }

    // Changement de thème
        const themeToggle = document.getElementById('themeToggle');
        if (themeToggle) {
            themeToggle.addEventListener('click', () => {
                this.toggleTheme();
            });
        }

    // Notifications
        const notificationBtn = document.getElementById('notificationBtn');
        const notificationsPanel = document.getElementById('notificationsPanel');
        const closeNotifications = document.getElementById('closeNotifications');

        if (notificationBtn) {
            notificationBtn.addEventListener('click', () => {
                notificationsPanel.classList.add('open');
            });
        }

        if (closeNotifications) {
            closeNotifications.addEventListener('click', () => {
                notificationsPanel.classList.remove('open');
            });
        }

    // Onglets de filtre commandes
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const filter = e.currentTarget.dataset.filter;
                this.setActiveFilter(filter);
                this.loadOrders();
            });
        });

    // Fermer les notifications en cliquant à l'extérieur
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.notifications-panel') && 
                !e.target.closest('.notification-btn')) {
                notificationsPanel.classList.remove('open');
            }
        });

    // Fermer la sidebar sur mobile en cliquant à l'extérieur
        document.addEventListener('click', (e) => {
            if (window.innerWidth <= 768 && 
                !e.target.closest('.sidebar') && 
                !e.target.closest('.mobile-menu-btn')) {
                sidebar.classList.remove('open');
            }
        });
    }

    showSection(sectionId) {
        // Met à jour la navigation
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.remove('active');
        });
        document.querySelector(`[data-section="${sectionId}"]`).classList.add('active');

    // Met à jour le contenu
        document.querySelectorAll('.content-section').forEach(section => {
            section.classList.remove('active');
        });
        document.getElementById(sectionId).classList.add('active');

    // Met à jour le titre de la page
        const titles = {
            dashboard: 'Tableau de bord',
            orders: 'Gestion des commandes',
            map: 'Carte et itinéraires',
            stats: 'Statistiques',
            profile: 'Mon profil'
        };
        document.querySelector('.page-title').textContent = titles[sectionId];

        this.currentSection = sectionId;

    // Ferme la sidebar sur mobile
        if (window.innerWidth <= 768) {
            document.getElementById('sidebar').classList.remove('open');
        }
    }

    setActiveFilter(filter) {
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        document.querySelector(`[data-filter="${filter}"]`).classList.add('active');
        this.currentFilter = filter;
    }

    toggleTheme() {
        this.theme = this.theme === 'light' ? 'dark' : 'light';
        localStorage.setItem('theme', this.theme);
        this.applyTheme();
        
        // Update icon
        const icon = document.querySelector('#themeToggle i');
        icon.className = this.theme === 'light' ? 'fas fa-moon' : 'fas fa-sun';
    }

    initializeTheme() {
        this.applyTheme();
        const icon = document.querySelector('#themeToggle i');
        icon.className = this.theme === 'light' ? 'fas fa-moon' : 'fas fa-sun';
    }

    applyTheme() {
        document.documentElement.setAttribute('data-theme', this.theme);
    }

    loadRecentOrders() {
        // Charge les commandes récentes
        const container = document.getElementById('recentOrders');
        if (!container) return;

        const recentOrders = this.sampleOrders
            .filter(order => order.status === 'pending')
            .slice(0, 4);

        container.innerHTML = recentOrders.map(order => `
            <div class="order-item">
                <div class="order-info">
                    <h4>Commande #${order.id}</h4>
                    <p>${order.customer} • ${order.time}</p>
                </div>
                <div class="order-status status-${order.status}">
                    ${this.getStatusText(order.status)}
                </div>
            </div>
        `).join('');
    }

    loadOrders() {
        const container = document.getElementById('ordersContainer');
        if (!container) return;

        let filteredOrders = this.sampleOrders;
        if (this.currentFilter !== 'all') {
            filteredOrders = this.sampleOrders.filter(order => order.status === this.currentFilter);
        }

        container.innerHTML = filteredOrders.map(order => `
            <div class="order-card">
                <div class="order-details">
                    <h3>Commande #${order.id}</h3>
                    <div class="order-meta">
                        <span><i class="fas fa-user"></i> ${order.customer}</span>
                        <span><i class="fas fa-clock"></i> ${order.time}</span>
                        <span><i class="fas fa-money-bill-wave"></i> ${order.amount.toLocaleString()} FCFA</span>
                        <span><i class="fas fa-box"></i> ${order.items} article(s)</span>
                    </div>
                    <div class="order-address">
                        <i class="fas fa-map-marker-alt"></i> ${order.address}
                    </div>
                </div>
                <div class="order-actions">
                    ${this.getOrderActions(order.status, order.id)}
                </div>
            </div>
        `).join('');

    // Ajoute les listeners sur les boutons d'action
    this.setupOrderActions();
    }

    getOrderActions(status, orderId) {
        switch (status) {
            case 'pending':
                return `
                    <button class="btn-action btn-accept" data-action="accept" data-order="${orderId}">
                        Accepter
                    </button>
                    <button class="btn-action btn-route" data-action="route" data-order="${orderId}">
                        <i class="fas fa-route"></i> Itinéraire
                    </button>
                    <button class="btn-action btn-details" data-action="details" data-order="${orderId}">
                        Détails
                    </button>
                `;
            case 'in-progress':
                return `
                    <button class="btn-action btn-accept" data-action="complete" data-order="${orderId}">
                        Terminer
                    </button>
                    <button class="btn-action btn-route" data-action="route" data-order="${orderId}">
                        <i class="fas fa-route"></i> Itinéraire
                    </button>
                    <button class="btn-action btn-details" data-action="call" data-order="${orderId}">
                        Appeler
                    </button>
                `;
            case 'completed':
                return `
                    <button class="btn-action btn-route" data-action="route" data-order="${orderId}">
                        <i class="fas fa-route"></i> Voir trajet
                    </button>
                    <button class="btn-action btn-details" data-action="details" data-order="${orderId}">
                        Voir détails
                    </button>
                `;
            default:
                return '';
        }
    }

    setupOrderActions() {
        // Ajoute les listeners sur les boutons d'action
        document.querySelectorAll('.btn-action').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const action = e.target.dataset.action;
                const orderId = e.target.dataset.order;
                this.handleOrderAction(action, orderId);
            });
        });
    }

    handleOrderAction(action, orderId) {
        const order = this.sampleOrders.find(o => o.id === orderId);
        if (!order) return;

        switch (action) {
            case 'accept':
                order.status = 'in-progress';
                this.showNotification('Commande acceptée', 'success');
                this.loadOrders();
                this.loadRecentOrders();
                break;
            case 'complete':
                order.status = 'completed';
                this.showNotification('Livraison terminée', 'success');
                this.loadOrders();
                this.loadRecentOrders();
                break;
            case 'call':
                this.showNotification(`Appel vers ${order.phone}`, 'info');
                break;
            case 'details':
                this.showOrderDetails(order);
                break;
            case 'route':
                this.showRouteModal(order);
                break;
        }
    }

    showOrderDetails(order) {
        alert(`Détails de la commande #${order.id}\n\nClient: ${order.customer}\nAdresse: ${order.address}\nMontant: ${order.amount.toLocaleString()} FCFA\nStatut: ${this.getStatusText(order.status)}`);
    }

    showNotification(message, type = 'info') {
        // Crée une notification temporaire
        const notification = document.createElement('div');
        notification.className = `notification-toast ${type}`;
        notification.textContent = message;
        notification.style.cssText = `
            position: fixed;
            top: 100px;
            right: 20px;
            background: var(--${type === 'success' ? 'success' : type === 'error' ? 'error' : 'primary'}-color);
            color: white;
            padding: 1rem;
            border-radius: 8px;
            z-index: 3000;
            animation: slideInRight 0.3s ease-out;
        `;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 3000);
    }

    getStatusText(status) {
        const statusMap = {
            pending: 'En attente',
            'in-progress': 'En cours',
            completed: 'Terminé'
        };
        return statusMap[status] || status;
    }

    updateNotificationCount() {
        const badge = document.querySelector('.notification-badge');
        if (badge) {
            const unreadCount = document.querySelectorAll('.notification-item.unread').length;
            badge.textContent = unreadCount;
            badge.style.display = unreadCount > 0 ? 'flex' : 'none';
        }
    }

    showRouteModal(order) {
        // Crée la fenêtre modale d'itinéraire
        const modalOverlay = document.createElement('div');
        modalOverlay.className = 'modal-overlay';
        modalOverlay.innerHTML = `
            <div class="route-modal">
                <div class="modal-header">
                    <h3><i class="fas fa-route"></i> Itinéraire - Commande #${order.id}</h3>
                    <button class="close-modal-btn">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="modal-content">
                    <div class="route-info-section">
                        <div class="destination-info">
                            <h4><i class="fas fa-map-marker-alt"></i> Destination</h4>
                            <p class="address">${order.address}</p>
                            <p class="customer-name">Client: ${order.customer}</p>
                            <p class="phone-number">
                                <i class="fas fa-phone"></i> ${order.phone}
                                <button class="btn-call" onclick="window.open('tel:${order.phone}')">
                                    Appeler
                                </button>
                            </p>
                        </div>
                        
                        <div class="route-details">
                            <div class="route-stat">
                                <i class="fas fa-route"></i>
                                <span>Distance: ${this.calculateDistance()} km</span>
                            </div>
                            <div class="route-stat">
                                <i class="fas fa-clock"></i>
                                <span>Temps estimé: ${this.calculateTime()} min</span>
                            </div>
                            <div class="route-stat">
                                <i class="fas fa-gas-pump"></i>
                                <span>Carburant: ~${this.calculateFuel()}L</span>
                            </div>
                        </div>
                    </div>
                    
                    <div class="map-section">
                        <div class="route-map">
                            <div class="map-placeholder">
                                <i class="fas fa-map-marked-alt"></i>
                                <h4>Carte interactive</h4>
                                <p>Trajet optimisé vers la destination</p>
                                <div class="route-points">
                                    <div class="point start">
                                        <i class="fas fa-play-circle"></i>
                                        <span>Départ: Votre position</span>
                                    </div>
                                    <div class="route-line"></div>
                                    <div class="point end">
                                        <i class="fas fa-flag-checkered"></i>
                                        <span>Arrivée: ${order.address}</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="route-actions">
                        <button class="btn-primary btn-navigate" onclick="this.openGoogleMaps('${order.address}')">
                            <i class="fas fa-directions"></i> Ouvrir dans Google Maps
                        </button>
                        <button class="btn-secondary btn-waze" onclick="this.openWaze('${order.address}')">
                            <i class="fas fa-route"></i> Ouvrir dans Waze
                        </button>
                        ${order.status === 'in-progress' ? `
                            <button class="btn-success btn-arrived" data-order="${order.id}">
                                <i class="fas fa-check-circle"></i> Je suis arrivé
                            </button>
                        ` : ''}
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modalOverlay);
        
    // Ajoute les listeners de fermeture
        modalOverlay.querySelector('.close-modal-btn').addEventListener('click', () => {
            modalOverlay.remove();
        });
        
        modalOverlay.addEventListener('click', (e) => {
            if (e.target === modalOverlay) {
                modalOverlay.remove();
            }
        });
        
        const arrivedBtn = modalOverlay.querySelector('.btn-arrived');
        if (arrivedBtn) {
            arrivedBtn.addEventListener('click', (e) => {
                const orderId = e.target.dataset.order;
                this.markAsArrived(orderId);
                modalOverlay.remove();
            });
        }
        
    // Ajoute les méthodes de navigation aux boutons
        modalOverlay.querySelector('.btn-navigate').onclick = () => this.openGoogleMaps(order.address);
        modalOverlay.querySelector('.btn-waze').onclick = () => this.openWaze(order.address);
    }
    
    calculateDistance() {
        return (Math.random() * 10 + 2).toFixed(1);
    }
    
    calculateTime() {
        return Math.floor(Math.random() * 20 + 10);
    }
    
    calculateFuel() {
        return (Math.random() * 2 + 0.5).toFixed(1);
    }
    
    openGoogleMaps(address) {
        const encodedAddress = encodeURIComponent(address);
        window.open(`https://www.google.com/maps/dir/?api=1&destination=${encodedAddress}`, '_blank');
    }
    
    openWaze(address) {
        const encodedAddress = encodeURIComponent(address);
        window.open(`https://waze.com/ul?q=${encodedAddress}&navigate=yes`, '_blank');
    }
    
    markAsArrived(orderId) {
        this.showNotification('Position confirmée - Vous êtes arrivé à destination', 'success');
        // Ici on pourrait mettre à jour le statut ou envoyer la position au serveur
    }

    // Simulate real-time updates
    simulateRealTimeUpdates() {
        // Simule les mises à jour en temps réel
        setInterval(() => {
            // Met à jour aléatoirement le statut des commandes
            if (Math.random() > 0.8) {
                const pendingOrders = this.sampleOrders.filter(o => o.status === 'pending');
                if (pendingOrders.length > 0) {
                    const randomOrder = pendingOrders[Math.floor(Math.random() * pendingOrders.length)];
                    randomOrder.status = 'in-progress';
                    this.loadOrders();
                    this.loadRecentOrders();
                    this.showNotification(`Commande #${randomOrder.id} mise à jour`, 'info');
                }
            }
        }, 30000); // Toutes les 30 secondes
    }
}

// Fonction globale pour le bouton carte
function showSection(sectionId) {
    window.dashboard.showSection(sectionId);
}

// Initialise le tableau de bord quand le DOM est chargé
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new DeliveryDashboard();
    // Lance la simulation temps réel après un délai
    setTimeout(() => {
        window.dashboard.simulateRealTimeUpdates();
    }, 5000);
});

// Gère le redimensionnement de la fenêtre
window.addEventListener('resize', () => {
    const sidebar = document.getElementById('sidebar');
    if (window.innerWidth > 768) {
        sidebar.classList.remove('open');
    }
});
