// ========================================
// GLOBAL STATE & CONFIG
// ========================================
const API_BASE = '/api';
let currentUser = null;

// ========================================
// UTILITY FUNCTIONS
// ========================================
function showAlert(message, type = 'info') {
    alert(message);
}

function getCurrentUser() {
    const userStr = localStorage.getItem('currentUser');
    return userStr ? JSON.parse(userStr) : null;
}

function setCurrentUser(user) {
    localStorage.setItem('currentUser', JSON.stringify(user));
    currentUser = user;
}

function clearCurrentUser() {
    localStorage.removeItem('currentUser');
    currentUser = null;
}

function checkAuth() {
    const user = getCurrentUser();
    if (!user) {
        window.location.href = '/login';
        return null;
    }
    return user;
}

// ========================================
// AUTHENTICATION
// ========================================

// Register Form Handler
if (document.getElementById('registerForm')) {
    document.getElementById('registerForm').addEventListener('submit', async (e) => {
        e.preventDefault();

        const username = document.getElementById('username').value;
        const email = document.getElementById('email').value;
        const password = document.getElementById('password').value;
        const confirmPassword = document.getElementById('confirmPassword').value;
        const birthdate = document.getElementById('birthdate').value;

        // Validate passwords match
        if (password !== confirmPassword) {
            showAlert('Passwords do not match!', 'error');
            return;
        }

        try {
            const response = await fetch(`${API_BASE}/register`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, email, password, birthdate })
            });

            const data = await response.json();

            if (response.ok) {
                showAlert(`Registration successful! ${data.message}`, 'success');
                setTimeout(() => {
                    window.location.href = '/login';
                }, 1500);
            } else {
                showAlert(data.error || 'Registration failed', 'error');
            }
        } catch (error) {
            console.error('Register error:', error);
            showAlert('Network error. Please try again.', 'error');
        }
    });
}

// Login Form Handler
if (document.getElementById('loginForm')) {
    document.getElementById('loginForm').addEventListener('submit', async (e) => {
        e.preventDefault();

        const email = document.getElementById('email').value;
        const password = document.getElementById('password').value;

        try {
            const response = await fetch(`${API_BASE}/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password })
            });

            const data = await response.json();

            if (response.ok) {
                // Store user data in localStorage
                setCurrentUser(data.user);
                showAlert('Login successful!', 'success');
                setTimeout(() => {
                    window.location.href = '/dashboard';
                }, 500);
            } else {
                showAlert(data.error || 'Login failed', 'error');
            }
        } catch (error) {
            console.error('Login error:', error);
            showAlert('Network error. Please try again.', 'error');
        }
    });
}

// Logout Function
function logout() {
    if (confirm('Are you sure you want to logout?')) {
        clearCurrentUser();
        window.location.href = '/login';
    }
}

// ========================================
// DASHBOARD
// ========================================
if (window.location.pathname === '/dashboard') {
    document.addEventListener('DOMContentLoaded', async () => {
        const user = checkAuth();
        if (!user) return;

        // Display username
        document.getElementById('userName').textContent = user.username;

        // Load statistics
        await loadUserStats(user.user_id);

        // Load recent dreams
        await loadRecentDreams(user.user_id);
    });
}

async function loadUserStats(userId) {
    try {
        const response = await fetch(`${API_BASE}/stats/user/${userId}`);
        const stats = await response.json();

        if (response.ok) {
            document.getElementById('totalDreams').textContent = stats.total_dreams;
            document.getElementById('lucidDreams').textContent = stats.lucid_dreams;
            document.getElementById('avgIntensity').textContent = stats.average_intensity.toFixed(1);
            document.getElementById('lucidPercentage').textContent = stats.lucid_percentage.toFixed(1) + '%';
        }
    } catch (error) {
        console.error('Stats error:', error);
    }
}

async function loadRecentDreams(userId) {
    try {
        const response = await fetch(`${API_BASE}/dreams/user/${userId}`);
        const dreams = await response.json();

        const container = document.getElementById('recentDreams');

        if (response.ok && dreams.length > 0) {
            container.innerHTML = dreams.slice(0, 5).map(dream => `
                <div class="dream-item" style="padding: 1rem; border-bottom: 1px solid var(--border); cursor: pointer;">
                    <div style="display: flex; justify-content: space-between; align-items: start;">
                        <div>
                            <h4 style="margin: 0 0 0.5rem 0;">${dream.dname}</h4>
                            <p class="text-muted" style="margin: 0; font-size: 0.875rem;">
                                ${dream.description.substring(0, 100)}${dream.description.length > 100 ? '...' : ''}
                            </p>
                            <div style="margin-top: 0.5rem;">
                                <span class="badge" style="background: var(--primary); color: white; padding: 0.25rem 0.5rem; border-radius: 0.25rem; font-size: 0.75rem;">
                                    Intensity: ${dream.intensity}/10
                                </span>
                                ${dream.lucid ? '<span class="badge" style="background: var(--success); color: white; padding: 0.25rem 0.5rem; border-radius: 0.25rem; font-size: 0.75rem; margin-left: 0.5rem;">✨ Lucid</span>' : ''}
                            </div>
                        </div>
                        <div style="text-align: right;">
                            <p class="text-muted" style="margin: 0; font-size: 0.875rem;">${new Date(dream.dream_date).toLocaleDateString()}</p>
                            <button onclick="deleteDream(${dream.dream_id})" class="btn btn-danger" style="margin-top: 0.5rem; padding: 0.25rem 0.75rem; font-size: 0.875rem;">
                                Delete
                            </button>
                        </div>
                    </div>
                </div>
            `).join('');
        } else {
            container.innerHTML = '<p class="text-muted">No dreams recorded yet. Start by adding your first dream!</p>';
        }
    } catch (error) {
        console.error('Dreams error:', error);
        document.getElementById('recentDreams').innerHTML = '<p class="text-muted">Error loading dreams.</p>';
    }
}

async function deleteDream(dreamId) {
    if (!confirm('Are you sure you want to delete this dream?')) return;

    try {
        const response = await fetch(`${API_BASE}/dreams/${dreamId}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            showAlert('Dream deleted successfully!', 'success');
            const user = getCurrentUser();
            await loadRecentDreams(user.user_id);
            await loadUserStats(user.user_id);
        } else {
            showAlert('Failed to delete dream', 'error');
        }
    } catch (error) {
        console.error('Delete error:', error);
        showAlert('Network error', 'error');
    }
}

// ========================================
// ADD DREAM
// ========================================
if (window.location.pathname === '/add-dream') {
    document.addEventListener('DOMContentLoaded', async () => {
        const user = checkAuth();
        if (!user) return;

        // Set today's date as default
        document.getElementById('dream_date').valueAsDate = new Date();

        // Load emotions, themes, categories
        await loadTags();
    });

    document.getElementById('addDreamForm').addEventListener('submit', async (e) => {
        e.preventDefault();

        const user = getCurrentUser();
        const formData = {
            user_id: user.user_id,
            dname: document.getElementById('dname').value,
            description: document.getElementById('description').value,
            dream_date: document.getElementById('dream_date').value,
            intensity: parseInt(document.getElementById('intensity').value),
            lucid: document.getElementById('lucid').checked,
            emotions: getSelectedTags('emotion'),
            themes: getSelectedTags('theme'),
            categories: getSelectedTags('category')
        };

        try {
            const response = await fetch(`${API_BASE}/dreams`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData)
            });

            const data = await response.json();

            if (response.ok) {
                showAlert('Dream saved successfully!', 'success');
                setTimeout(() => {
                    window.location.href = '/dashboard';
                }, 1000);
            } else {
                showAlert(data.error || 'Failed to save dream', 'error');
            }
        } catch (error) {
            console.error('Save dream error:', error);
            showAlert('Network error', 'error');
        }
    });
}

async function loadTags() {
    try {
        // Load emotions
        const emotionsRes = await fetch(`${API_BASE}/emotions`);
        const emotions = await emotionsRes.json();
        renderTags('emotionTags', emotions, 'emotion', 'emotion_id', 'emotion_type');

        // Load themes
        const themesRes = await fetch(`${API_BASE}/themes`);
        const themes = await themesRes.json();
        renderTags('themeTags', themes, 'theme', 'theme_id', 'theme_name');

        // Load categories
        const categoriesRes = await fetch(`${API_BASE}/categories`);
        const categories = await categoriesRes.json();
        renderTags('categoryTags', categories, 'category', 'category_id', 'category_name');

    } catch (error) {
        console.error('Load tags error:', error);
    }
}

function renderTags(containerId, items, type, idKey, nameKey) {
    const container = document.getElementById(containerId);
    if (!container) return;

    if (items.length === 0) {
        container.innerHTML = '<p class="text-muted">No items available</p>';
        return;
    }

    container.innerHTML = `
        <div class="pill-grid">
            ${items.map(item => `
                <button type="button" 
                        class="pill-button" 
                        data-type="${type}" 
                        data-id="${item[idKey]}" 
                        onclick="togglePill(this)">
                    ${item[nameKey]}
                </button>
            `).join('')}
        </div>
    `;
}

function togglePill(element) {
    element.classList.toggle('selected');
}

function getSelectedTags(type) {
    const selected = document.querySelectorAll(`.pill-button.selected[data-type="${type}"]`);
    return Array.from(selected).map(pill => parseInt(pill.getAttribute('data-id')));
}

// ========================================
// CHAT / AI ANALYSIS
// ========================================
if (window.location.pathname === '/chat') {
    document.addEventListener('DOMContentLoaded', () => {
        const user = checkAuth();
        if (!user) return;
    });

    document.getElementById('chatForm').addEventListener('submit', async (e) => {
        e.preventDefault();

        const user = getCurrentUser();
        const input = document.getElementById('chatInput');
        const message = input.value.trim();

        if (!message) return;

        // Add user message to chat
        addMessageToChat(message, 'user');
        input.value = '';

        try {
            const response = await fetch(`${API_BASE}/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_id: user.user_id,
                    message: message
                })
            });

            const data = await response.json();

            if (response.ok) {
                addMessageToChat(data.reply, 'bot');
            } else if (data.premium_required) {
                addMessageToChat('⭐ This is a premium feature. Please subscribe to access AI dream analysis!', 'bot');
                setTimeout(() => {
                    window.location.href = '/subscription';
                }, 2000);
            } else {
                addMessageToChat('❌ Error: ' + (data.error || 'Failed to get response'), 'bot');
            }
        } catch (error) {
            console.error('Chat error:', error);
            addMessageToChat('❌ Network error. Please try again.', 'bot');
        }
    });
}

function addMessageToChat(text, sender) {
    const container = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message message-${sender}`;

    messageDiv.innerHTML = `
        <div class="message-avatar">${sender === 'user' ? '👤' : '🤖'}</div>
        <div class="message-content">
            <p>${text}</p>
        </div>
    `;

    container.appendChild(messageDiv);
    container.scrollTop = container.scrollHeight;
}

// ========================================
// SUBSCRIPTION PAGE
// ========================================
if (window.location.pathname === '/subscription') {
    document.addEventListener('DOMContentLoaded', async () => {
        const user = checkAuth();
        if (!user) return;

        await loadSubscriptionStatus(user.user_id);
    });
}

async function loadSubscriptionStatus(userId) {
    try {
        const response = await fetch(`${API_BASE}/subscription/${userId}`);
        const data = await response.json();

        const currentPlanDiv = document.getElementById('currentPlan');
        const cancelSection = document.getElementById('cancelSection');

        if (response.ok && data.has_subscription && data.is_active) {
            const sub = data.subscription;
            const endDate = new Date(sub.end_date).toLocaleDateString();

            currentPlanDiv.innerHTML = `
                <div class="alert alert-info" style="margin-bottom: 2rem;">
                    <h4>✅ Active Subscription</h4>
                    <p><strong>Plan:</strong> ${sub.plan_type}</p>
                    <p><strong>Status:</strong> ${sub.status}</p>
                    <p><strong>Valid Until:</strong> ${endDate}</p>
                    <p><strong>Auto-Renew:</strong> ${sub.auto_renew ? '✅ Enabled' : '❌ Disabled'}</p>
                </div>
            `;

            // Show cancel button if auto-renew is enabled
            if (sub.auto_renew) {
                cancelSection.style.display = 'block';
            }
        } else {
            currentPlanDiv.innerHTML = `
                <div class="alert alert-warning" style="margin-bottom: 2rem;">
                    <h4>📢 No Active Subscription</h4>
                    <p>Choose a plan below to unlock premium features!</p>
                </div>
            `;
            cancelSection.style.display = 'none';
        }
    } catch (error) {
        console.error('Subscription status error:', error);
    }
}

async function subscribe(planType, amount) {
    const user = getCurrentUser();
    if (!user) {
        showAlert('Please login first', 'error');
        window.location.href = '/login';
        return;
    }

    // Simulate payment method selection
    const paymentMethod = prompt('Enter payment method (e.g., CREDIT_CARD, PAYPAL):');
    if (!paymentMethod) return;

    try {
        const response = await fetch(`${API_BASE}/subscribe`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: user.user_id,
                plan_type: planType,
                payment_method: paymentMethod,
                amount: amount
            })
        });

        const data = await response.json();

        if (response.ok) {
            showAlert(`✅ Subscription activated! Welcome to ${planType} plan!`, 'success');
            
            // Update user subscription in localStorage
            user.subscription = {
                plan_type: planType,
                status: 'ACTIVE',
                end_date: data.end_date
            };
            setCurrentUser(user);

            // Reload subscription status
            await loadSubscriptionStatus(user.user_id);
        } else {
            showAlert(data.error || 'Subscription failed', 'error');
        }
    } catch (error) {
        console.error('Subscribe error:', error);
        showAlert('Network error. Please try again.', 'error');
    }
}

async function cancelSubscription() {
    const user = getCurrentUser();
    if (!user) return;

    if (!confirm('Are you sure you want to cancel auto-renewal? You will keep access until the end of your billing period.')) {
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/cancel-subscription`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: user.user_id })
        });

        const data = await response.json();

        if (response.ok) {
            showAlert('✅ Auto-renewal cancelled. You will keep access until ' + new Date(data.end_date).toLocaleDateString(), 'success');
            await loadSubscriptionStatus(user.user_id);
        } else {
            showAlert(data.error || 'Failed to cancel subscription', 'error');
        }
    } catch (error) {
        console.error('Cancel subscription error:', error);
        showAlert('Network error', 'error');
    }
}