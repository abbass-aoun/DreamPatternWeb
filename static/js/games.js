// ========================================
// GAMES & LEADERBOARD SYSTEM - FLAPPY BIRD ONLY
// ========================================

let currentGame = null;

// Submit game score
async function submitGameScore(gameName, score, level = 1, timePlayed = 0, metadata = {}) {
    const user = getCurrentUser();
    if (!user) {
        showAlert('Please login first', 'error');
        return;
    }

    console.log('Submitting score:', { gameName, score, level, user: user.username });

    try {
        const response = await fetch(`${API_BASE}/games/submit-score`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: user.user_id,
                game_name: gameName,
                score: score,
                level: level,
                time_played: timePlayed,
                metadata: metadata
            })
        });

        const data = await response.json();

        if (response.ok) {
            console.log('Score submitted successfully:', data);
            
            const message = data.is_personal_best 
                ? `🎉 New Personal Best! Rank #${data.rank} | +${data.xp_earned} XP, +${data.coins_earned} Coins`
                : `Score submitted! Rank #${data.rank} | +${data.xp_earned} XP, +${data.coins_earned} Coins`;
            showAlert(message, 'success');
            
            // Reload leaderboard after score submission
            setTimeout(() => {
                if (typeof loadLeaderboard === 'function') {
                    console.log('Reloading leaderboard...');
                    loadLeaderboard(gameName);
                }
            }, 500);
            
            // Reload game stats if available
            if (typeof loadGameStats === 'function') {
                await loadGameStats(user.user_id);
            }
        } else {
            console.error('Score submission failed:', data);
            showAlert(data.error || 'Failed to submit score', 'error');
        }
    } catch (error) {
        console.error('Submit score error:', error);
        showAlert('Network error', 'error');
    }
}

// Load leaderboard for a game
async function loadLeaderboard(gameName, limit = 100) {
    console.log('=== LOADING LEADERBOARD ===');
    console.log('Game:', gameName);
    
    try {
        const url = `${API_BASE}/games/leaderboard/${gameName}?limit=${limit}`;
        console.log('Fetching from:', url);
        
        const response = await fetch(url);
        const data = await response.json();
        
        console.log('Leaderboard response:', data);

        if (response.ok && document.getElementById('leaderboardContent')) {
            const container = document.getElementById('leaderboardContent');
            
            if (!data.leaderboard || data.leaderboard.length === 0) {
                console.log('No leaderboard entries found');
                container.innerHTML = `
                    <div style="text-align: center; padding: 3rem;">
                        <div style="font-size: 4rem; margin-bottom: 1rem;">🎮</div>
                        <p style="font-size: 1.2rem; color: var(--text-muted);">No scores yet!</p>
                        <p style="color: var(--text-muted);">Be the first to play and claim the top spot!</p>
                    </div>
                `;
                return;
            }

            console.log(`Found ${data.leaderboard.length} leaderboard entries`);
            data.leaderboard.forEach((entry, i) => {
                console.log(`  ${i+1}. ${entry.username}: ${entry.score} points (Level ${entry.level})`);
            });

            const user = getCurrentUser();
            const userId = user ? user.user_id : null;
            console.log('Current user ID:', userId);

            // Sort by score descending
            const topScores = data.leaderboard.sort((a, b) => b.score - a.score);

            container.innerHTML = `
                <div style="margin-bottom: 2rem;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem;">
                        <h3 style="margin: 0; color: #e9d5ff;">
                            🏆 Top ${topScores.length} Players
                        </h3>
                        <div style="color: var(--text-muted); font-size: 0.875rem;">
                            ${new Date().toLocaleDateString()} ${new Date().toLocaleTimeString()}
                        </div>
                    </div>
                    
                    <div style="display: grid; gap: 0.75rem;">
                        ${topScores.map((entry, index) => {
                            const isCurrentUser = userId && entry.user_id === userId;
                            const medal = index === 0 ? '🥇' : index === 1 ? '🥈' : index === 2 ? '🥉' : '';
                            const rank = index + 1;
                            
                            return `
                                <div style="
                                    padding: 1.25rem;
                                    background: ${isCurrentUser 
                                        ? 'linear-gradient(135deg, rgba(99, 102, 241, 0.3), rgba(139, 92, 246, 0.3))' 
                                        : index < 3 
                                            ? 'linear-gradient(135deg, rgba(234, 179, 8, 0.1), rgba(202, 138, 4, 0.1))' 
                                            : 'rgba(30, 41, 59, 0.5)'};
                                    border-radius: 0.75rem;
                                    border: ${isCurrentUser 
                                        ? '2px solid rgba(99, 102, 241, 0.6)' 
                                        : index < 3 
                                            ? '1px solid rgba(234, 179, 8, 0.3)' 
                                            : '1px solid rgba(71, 85, 105, 0.3)'};
                                    display: grid;
                                    grid-template-columns: auto 1fr auto;
                                    gap: 1rem;
                                    align-items: center;
                                    transition: all 0.3s ease;
                                ">
                                    
                                    <!-- Rank -->
                                    <div style="
                                        display: flex;
                                        align-items: center;
                                        justify-content: center;
                                        min-width: 60px;
                                    ">
                                        ${medal 
                                            ? `<span style="font-size: 2.5rem;">${medal}</span>` 
                                            : `<span style="
                                                font-size: 1.5rem;
                                                font-weight: bold;
                                                color: ${isCurrentUser ? '#c084fc' : '#94a3b8'};
                                            ">#${rank}</span>`
                                        }
                                    </div>
                                    
                                    <!-- Player Info -->
                                    <div>
                                        <div style="
                                            font-size: 1.1rem;
                                            font-weight: ${isCurrentUser ? 'bold' : '600'};
                                            color: ${isCurrentUser ? '#c084fc' : '#e2e8f0'};
                                            margin-bottom: 0.25rem;
                                            display: flex;
                                            align-items: center;
                                            gap: 0.5rem;
                                        ">
                                            <span>${entry.username}</span>
                                            ${isCurrentUser ? '<span style="background: rgba(99, 102, 241, 0.3); padding: 0.25rem 0.5rem; border-radius: 0.25rem; font-size: 0.75rem; font-weight: 600;">YOU</span>' : ''}
                                        </div>
                                        <div style="
                                            font-size: 0.875rem;
                                            color: #94a3b8;
                                            display: flex;
                                            gap: 1rem;
                                            align-items: center;
                                        ">
                                            <span>🎯 Level ${entry.level || 1}</span>
                                            <span>📅 ${new Date(entry.created_at).toLocaleDateString()}</span>
                                        </div>
                                    </div>
                                    
                                    <!-- Score -->
                                    <div style="text-align: right;">
                                        <div style="
                                            font-size: 2rem;
                                            font-weight: bold;
                                            background: linear-gradient(135deg, #c084fc, #a855f7);
                                            -webkit-background-clip: text;
                                            -webkit-text-fill-color: transparent;
                                            background-clip: text;
                                            line-height: 1;
                                        ">
                                            ${entry.score.toLocaleString()}
                                        </div>
                                        <div style="
                                            font-size: 0.75rem;
                                            color: #94a3b8;
                                            margin-top: 0.25rem;
                                        ">
                                            POINTS
                                        </div>
                                    </div>
                                </div>
                            `;
                        }).join('')}
                    </div>
                </div>
                
                ${userId ? `
                    <div style="
                        margin-top: 2rem;
                        padding: 1rem;
                        background: rgba(99, 102, 241, 0.1);
                        border-radius: 0.5rem;
                        border: 1px solid rgba(99, 102, 241, 0.3);
                        text-align: center;
                    ">
                        <p style="margin: 0; color: #c084fc; font-weight: 600;">
                            ${topScores.findIndex(s => s.user_id === userId) >= 0 
                                ? `🎉 You're ranked #${topScores.findIndex(s => s.user_id === userId) + 1} with ${topScores.find(s => s.user_id === userId).score} points!`
                                : `Play now to get on the leaderboard!`
                            }
                        </p>
                    </div>
                ` : ''}
            `;
            
            console.log('Leaderboard rendered successfully');
        } else {
            console.error('Failed to load leaderboard:', data);
        }
    } catch (error) {
        console.error('Leaderboard error:', error);
        if (document.getElementById('leaderboardContent')) {
            document.getElementById('leaderboardContent').innerHTML = `
                <div style="text-align: center; padding: 3rem;">
                    <div style="font-size: 4rem; margin-bottom: 1rem;">❌</div>
                    <p style="font-size: 1.2rem; color: #ef4444;">Error loading leaderboard</p>
                    <p style="color: var(--text-muted);">${error.message}</p>
                    <button class="btn btn-primary" onclick="refreshLeaderboard()" style="margin-top: 1rem;">
                        Try Again
                    </button>
                </div>
            `;
        }
    }
}

// Load user's game scores
async function loadUserScores(userId) {
    try {
        const response = await fetch(`${API_BASE}/games/user-scores/${userId}`);
        const data = await response.json();

        if (response.ok && document.getElementById('userScores')) {
            const container = document.getElementById('userScores');
            
            // Filter to show only Flappy Bird
            const flappyScores = data.scores.filter(score => score.game_name === 'Flappy Bird');
            
            container.innerHTML = flappyScores.map(score => `
                <div class="card" style="margin-bottom: 1rem;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <h3 style="margin: 0 0 0.5rem 0;">
                                ${score.game_icon} ${score.game_name}
                            </h3>
                            ${score.best_score ? `
                                <p style="margin: 0; color: var(--text-muted);">
                                    Best Score: <strong style="color: var(--primary);">${score.best_score.toLocaleString()}</strong> 
                                    (Level ${score.best_level || 1})
                                </p>
                                <p style="margin: 0; font-size: 0.875rem; color: var(--text-muted);">
                                    Played ${score.total_plays} time${score.total_plays !== 1 ? 's' : ''}
                                    ${score.last_played ? ` • Last: ${new Date(score.last_played).toLocaleDateString()}` : ''}
                                </p>
                            ` : `
                                <p style="margin: 0; color: var(--text-muted);">Not played yet</p>
                            `}
                        </div>
                        <button 
                            class="btn btn-primary" 
                            onclick="showGame('${score.game_name}')"
                        >
                            Play
                        </button>
                    </div>
                </div>
            `).join('');
        }
    } catch (error) {
        console.error('User scores error:', error);
    }
}

// Get user's rank for a game
async function getUserRank(userId, gameName) {
    try {
        const response = await fetch(`${API_BASE}/games/user-rank/${userId}/${gameName}`);
        const data = await response.json();
        
        return data;
    } catch (error) {
        console.error('Get rank error:', error);
        return null;
    }
}

// Show specific game
function showGame(gameName) {
    currentGame = gameName;
    
    console.log('Showing game:', gameName);
    
    // Hide games list
    const gamesCategory = document.querySelector('.games-category');
    const gamesHeader = document.querySelector('.games-header');
    if (gamesCategory) gamesCategory.style.display = 'none';
    if (gamesHeader) gamesHeader.style.display = 'none';
    
    // Show game view
    const gameView = document.getElementById('gameView');
    if (gameView) gameView.style.display = 'block';
    
    // Hide all game containers first
    document.querySelectorAll('.game-container').forEach(container => {
        container.style.display = 'none';
    });
    
    // Show Flappy Bird
    if (gameName === 'Flappy Bird') {
        const flappyContainer = document.getElementById('flappybirdContainer');
        if (flappyContainer) {
            flappyContainer.style.display = 'block';
            
            // Initialize game after a short delay to ensure DOM is ready
            setTimeout(() => {
                const canvas = document.getElementById('flappyCanvas');
                if (canvas && typeof initFlappy === 'function') {
                    console.log('Starting Flappy Bird...');
                    initFlappy();
                } else {
                    console.error('Canvas or initFlappy function not found');
                }
            }, 200);
        } else {
            console.error('Flappy container not found');
        }
    }
}

function showLeaderboard(gameName) {
    const targetGame = gameName || currentGame;
    if (!targetGame) {
        console.error('No game specified for leaderboard');
        return;
    }
    
    console.log('Showing leaderboard for:', targetGame);
    
    const gamesGridParent = document.getElementById('gamesGrid')?.parentElement;
    const gameView = document.getElementById('gameView');
    const leaderboardView = document.getElementById('leaderboardView');
    
    if (gamesGridParent) gamesGridParent.style.display = 'none';
    if (gameView) gameView.style.display = 'none';
    if (leaderboardView) leaderboardView.style.display = 'block';
    
    // Load the leaderboard
    loadLeaderboard(targetGame);
}

function showGamesList() {
    const gamesGridParent = document.getElementById('gamesGrid')?.parentElement;
    const gameView = document.getElementById('gameView');
    const leaderboardView = document.getElementById('leaderboardView');
    const gamesHeader = document.querySelector('.games-header');
    
    if (gamesGridParent) gamesGridParent.style.display = 'block';
    if (gamesHeader) gamesHeader.style.display = 'block';
    if (gameView) gameView.style.display = 'none';
    if (leaderboardView) leaderboardView.style.display = 'none';
    
    currentGame = null;
}

// Refresh leaderboard
function refreshLeaderboard() {
    if (currentGame) {
        console.log('Refreshing leaderboard for:', currentGame);
        showAlert('Refreshing leaderboard...', 'info');
        loadLeaderboard(currentGame);
    }
}

// Load all games (filter to show only Flappy Bird)
async function loadGames() {
    try {
        const response = await fetch(`${API_BASE}/games`);
        const data = await response.json();

        if (response.ok && document.getElementById('gamesGrid')) {
            const container = document.getElementById('gamesGrid');
            
            // Filter to show only Flappy Bird
            const flappyBird = data.games.find(game => game.game_name === 'Flappy Bird');
            const games = flappyBird ? [flappyBird] : [];
            
            if (games.length === 0) {
                // Fallback if no games in database
                games.push({
                    game_name: 'Flappy Bird',
                    game_icon: '🐦',
                    game_description: 'Navigate through pipes and score points! Test your reflexes in this classic arcade game.'
                });
            }
            
            container.innerHTML = games.map(game => `
                <div class="game-card" onclick="showGame('${game.game_name}')">
                    <div class="game-icon">${game.game_icon}</div>
                    <h3 class="game-title">${game.game_name}</h3>
                    <p class="game-description">${game.game_description}</p>
                    <button class="play-button">Play Now</button>
                </div>
            `).join('');
        }
    } catch (error) {
        console.error('Load games error:', error);
        
        // Fallback to show Flappy Bird even if API fails
        if (document.getElementById('gamesGrid')) {
            document.getElementById('gamesGrid').innerHTML = `
                <div class="game-card" onclick="showGame('Flappy Bird')">
                    <div class="game-icon">🐦</div>
                    <h3 class="game-title">Flappy Bird</h3>
                    <p class="game-description">Navigate through pipes and score points! Test your reflexes in this classic arcade game.</p>
                    <button class="play-button">Play Now</button>
                </div>
            `;
        }
    }
}

// Show notification helper
function showAlert(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 1rem 1.5rem;
        background: ${type === 'success' ? '#10b981' : type === 'error' ? '#ef4444' : '#6366f1'};
        color: white;
        border-radius: 0.5rem;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        z-index: 10000;
        animation: slideIn 0.3s ease-out;
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease-out';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Get current user from localStorage
function getCurrentUser() {
    const userStr = localStorage.getItem('user');
    if (userStr) {
        try {
            return JSON.parse(userStr);
        } catch (e) {
            return null;
        }
    }
    return null;
}