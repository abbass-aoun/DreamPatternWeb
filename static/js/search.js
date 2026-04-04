// ========================================
// DREAM SEARCH & FILTER
// ========================================

let emotions = [];
let themes = [];
let categories = [];

document.addEventListener('DOMContentLoaded', async () => {
    const user = checkAuth();
    if (!user) {
        window.location.href = '/login';
        return;
    }
    await loadFilters();
    await performSearch(); // Load all dreams initially
});

async function loadFilters() {
    try {
        // Load emotions
        const emotionsRes = await fetch(`${API_BASE}/emotions`);
        const emotionsData = await emotionsRes.json();
        if (emotionsRes.ok) {
            emotions = emotionsData;
            const select = document.getElementById('emotionFilter');
            select.innerHTML = '<option value="">All Emotions</option>';
            emotions.forEach(emotion => {
                const option = document.createElement('option');
                option.value = emotion.emotion_id;
                option.textContent = emotion.emotion_type;
                select.appendChild(option);
            });
        }
        
        // Load themes
        const themesRes = await fetch(`${API_BASE}/themes`);
        const themesData = await themesRes.json();
        if (themesRes.ok) {
            themes = themesData;
            const select = document.getElementById('themeFilter');
            select.innerHTML = '<option value="">All Themes</option>';
            themes.forEach(theme => {
                const option = document.createElement('option');
                option.value = theme.theme_id;
                option.textContent = theme.theme_name;
                select.appendChild(option);
            });
        }
        
        // Load categories
        const categoriesRes = await fetch(`${API_BASE}/categories`);
        const categoriesData = await categoriesRes.json();
        if (categoriesRes.ok) {
            categories = categoriesData;
            const select = document.getElementById('categoryFilter');
            select.innerHTML = '<option value="">All Categories</option>';
            categories.forEach(category => {
                const option = document.createElement('option');
                option.value = category.category_id;
                option.textContent = category.category_name;
                select.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Load filters error:', error);
    }
}

function handleSearch(event) {
    if (event.key === 'Enter') {
        performSearch();
    }
}

async function performSearch() {
    const user = getCurrentUser();
    if (!user) return;
    
    try {
        const params = new URLSearchParams();
        
        const query = document.getElementById('searchQuery').value;
        if (query) params.append('q', query);
        
        const startDate = document.getElementById('startDate').value;
        if (startDate) params.append('start_date', startDate);
        
        const endDate = document.getElementById('endDate').value;
        if (endDate) params.append('end_date', endDate);
        
        const lucid = document.getElementById('lucidFilter').value;
        if (lucid) params.append('lucid', lucid);
        
        const minIntensity = document.getElementById('minIntensity').value;
        if (minIntensity) params.append('min_intensity', minIntensity);
        
        const maxIntensity = document.getElementById('maxIntensity').value;
        if (maxIntensity) params.append('max_intensity', maxIntensity);
        
        const emotionId = document.getElementById('emotionFilter').value;
        if (emotionId) params.append('emotion_id', emotionId);
        
        const themeId = document.getElementById('themeFilter').value;
        if (themeId) params.append('theme_id', themeId);
        
        const categoryId = document.getElementById('categoryFilter').value;
        if (categoryId) params.append('category_id', categoryId);
        
        const response = await fetch(`${API_BASE}/search/dreams/${user.user_id}?${params.toString()}`);
        const data = await response.json();
        
        if (response.ok) {
            displayResults(data.dreams || []);
            document.getElementById('resultsCount').textContent = data.count || 0;
        } else {
            showAlert(data.error || 'Search failed', 'error');
        }
    } catch (error) {
        console.error('Search error:', error);
        showAlert('Network error', 'error');
    }
}

function displayResults(dreams) {
    const grid = document.getElementById('resultsGrid');
    
    if (dreams.length === 0) {
        grid.innerHTML = '<p class="text-muted text-center">No dreams found matching your criteria</p>';
        return;
    }
    
    grid.innerHTML = dreams.map(dream => `
        <div class="dream-card">
            <h4>${dream.dname} ${dream.lucid ? '⭐' : ''}</h4>
            <div class="dream-card-meta">
                <span>📅 ${new Date(dream.dream_date).toLocaleDateString()}</span>
                ${dream.intensity ? `<span>⚡ Intensity: ${dream.intensity}</span>` : ''}
            </div>
            <div class="dream-card-description">
                ${dream.description.substring(0, 150)}${dream.description.length > 150 ? '...' : ''}
            </div>
            <div style="margin-top: 1rem;">
                <a href="/dream-detail?id=${dream.dream_id}" class="btn btn-primary" style="padding: 0.5rem 1rem;">View Details</a>
            </div>
        </div>
    `).join('');
}

function clearFilters() {
    document.getElementById('searchQuery').value = '';
    document.getElementById('startDate').value = '';
    document.getElementById('endDate').value = '';
    document.getElementById('lucidFilter').value = '';
    document.getElementById('minIntensity').value = '';
    document.getElementById('maxIntensity').value = '';
    document.getElementById('emotionFilter').value = '';
    document.getElementById('themeFilter').value = '';
    document.getElementById('categoryFilter').value = '';
    performSearch();
}

// Auto-search on filter change
document.getElementById('startDate').addEventListener('change', performSearch);
document.getElementById('endDate').addEventListener('change', performSearch);
document.getElementById('lucidFilter').addEventListener('change', performSearch);
document.getElementById('minIntensity').addEventListener('change', performSearch);
document.getElementById('maxIntensity').addEventListener('change', performSearch);
document.getElementById('emotionFilter').addEventListener('change', performSearch);
document.getElementById('themeFilter').addEventListener('change', performSearch);
document.getElementById('categoryFilter').addEventListener('change', performSearch);




















