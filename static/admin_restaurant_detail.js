

document.addEventListener('DOMContentLoaded', function () {

    const chatBox = document.getElementById('chat-box');
    if (chatBox) chatBox.scrollTop = chatBox.scrollHeight;

    // Load detailed data from shared context
    loadRestaurantDetail();
});

function loadRestaurantDetail() {
    if (typeof restaurant === 'undefined' || !restaurant) {
        console.warn('Restaurant data is missing from context');
        return;
    }

    // Populate profile information
    const setText = (id, text) => {
        const el = document.getElementById(id);
        if (el) el.textContent = text || 'Non renseigné';
    };

    setText('restaurant-name', restaurant.name);
    setText('restaurant-location', restaurant.location);
    setText('restaurant-rating', restaurant.rating);
    setText('restaurant-cuisine', restaurant.cuisine);
    setText('restaurant-phone', restaurant.phone);
    setText('restaurant-email', restaurant.email);
    setText('restaurant-address', restaurant.address);
    setText('restaurant-description', restaurant.description);
    setText('restaurant-price', convertPriceToTND(restaurant.price));

    const imageEl = document.getElementById('restaurant-image');
    if (imageEl) {
        if (restaurant.image && restaurant.image !== "") {
            imageEl.src = restaurant.image;
            imageEl.style.display = 'block';
            const placeholder = document.getElementById('restaurant-image-placeholder');
            if (placeholder) placeholder.style.display = 'none';
        } else {
            imageEl.style.display = 'none';
            const placeholder = document.getElementById('restaurant-image-placeholder');
            if (placeholder) placeholder.style.display = 'flex';
        }
    }

    const statusElement = document.getElementById('restaurant-status');
    let statusText = getStatusText(restaurant.status);

    const approveBtn = document.getElementById('btn-approve');
    if (restaurant.status === 'approved') {
        if (approveBtn) approveBtn.style.display = 'none';
    } else if (approveBtn) {
        approveBtn.style.display = 'block';
    }

    if (restaurant.payment_status === 'paid') {
        statusText += ' & Payé';
    } else {
        statusText += ' & Non payé';
    }

    statusElement.textContent = statusText;
    statusElement.className = `status-badge status-${restaurant.status}`;

    // Populate Menu
    const menuContainer = document.getElementById('restaurant-menu');
    if (restaurant.menu && restaurant.menu.length > 0) {
        menuContainer.innerHTML = restaurant.menu.map(item => `
            <div class="menu-item">
                <span class="menu-item-name">${item.name}</span>
                <span class="menu-item-price">${item.price}</span>
            </div>
        `).join('');
    } else {
        menuContainer.innerHTML = '<p style="color: #999; font-style: italic; text-align: center;">Aucune donnée disponible</p>';
    }

    // Populate Reviews
    const reviewsContainer = document.getElementById('restaurant-reviews');
    if (restaurant.reviews && restaurant.reviews.length > 0) {
        reviewsContainer.innerHTML = restaurant.reviews.map(review => `
            <div class="review-item">
                <span class="review-user">${review.user}</span>
                <span class="review-rating">${'★'.repeat(review.rating)}</span>
                <p class="review-comment">${review.comment}</p>
            </div>
        `).join('');
    } else {
        reviewsContainer.innerHTML = '<p style="color: #999; font-style: italic; text-align: center;">Aucune donnée disponible</p>';
    }

    // --- PAYMENT CONTROL ---
    syncPaymentStatus();
}

function syncPaymentStatus() {
    const paymentElement = document.getElementById('restaurant-payment');
    const approveBtn = document.getElementById('btn-approve');
    const payLinkBtn = document.getElementById('btn-pay-link');

    if (restaurant.payment_status === 'paid') {
        paymentElement.textContent = 'Payé (50 DT)';
        paymentElement.className = 'status-badge status-approved';
        payLinkBtn.style.display = 'none';
        
        // Only enable if not already approved
        if (approveBtn && restaurant.status !== 'approved') {
            approveBtn.disabled = false;
            approveBtn.title = "Restaurant éligible à l'approbation";
        }
    } else {
        paymentElement.textContent = 'Non payé';
        paymentElement.className = 'status-badge status-pending';
        payLinkBtn.style.display = 'block';
        if (approveBtn) {
            approveBtn.disabled = true;
            approveBtn.title = "Le paiement doit être effectué avant l'approbation";
        }
    }
}

async function sendPaymentLink() {
    const btn = document.getElementById('btn-pay-link');
    const originalText = btn.innerHTML;
    
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Envoi...';

    try {
        const response = await fetch('/api/send-payment-link/', {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken') 
            },
            body: JSON.stringify({ restaurant_id: restaurant.id })
        });
        
        if (response.ok) {
            location.reload(); // Refresh to show message in chat
        } else {
            alert("Erreur lors de l'envoi du lien.");
            btn.disabled = false;
            btn.innerHTML = originalText;
        }
    } catch (e) {
        console.error('API Error:', e);
        btn.disabled = false;
        btn.innerHTML = originalText;
    }
}

async function updateRestaurantStatus(status) {
    if (!confirm(`Voulez-vous vraiment passer le restaurant en statut "${getStatusText(status)}"?`)) return;

    try {
        const response = await fetch('/api/update-restaurant-status/', {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken') 
            },
            body: JSON.stringify({ 
                restaurant_id: restaurant.id, 
                status: status 
            })
        });
        
        if (response.ok) {
            location.reload();
        } else {
            const data = await response.json();
            alert(`Erreur : ${data.error}`);
        }
    } catch (e) {
        console.error('API Error:', e);
    }
}

// Helpers
function getStatusText(status) {
    const map = { 
        'pending': 'En attente', 
        'approved': 'Approuvé', 
        'rejected': 'Rejeté', 
        'suspended': 'Suspendu' 
    };
    return map[status] || status;
}

function convertPriceToTND(priceSymbol) {
    const map = { 
        "$": "Moins de 30 DT", 
        "$$": "30-80 DT", 
        "$$$": "80-150 DT", 
        "$$$$": "150+ DT" 
    };
    return map[priceSymbol] || priceSymbol;
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
