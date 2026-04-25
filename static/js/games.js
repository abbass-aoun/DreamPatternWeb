// ========================================
// GAMES & LEADERBOARD SYSTEM
// ========================================

let currentGame = null;
let leaderboardMode = 'game'; // game | global

async function readApiJson(response) {
    const text = await response.text();
    if (!text) return {};
    try {
        return JSON.parse(text);
    } catch {
        return { error: `Server returned ${response.status} (invalid JSON).` };
    }
}

function escapeHtml(value) {
    return String(value ?? '')
        .replaceAll('&', '&amp;')
        .replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;')
        .replaceAll('"', '&quot;')
        .replaceAll("'", '&#39;');
}

async function submitGameScore(gameName, score, level = 1, timePlayed = 0, metadata = {}) {
    const user = getCurrentUser();
    if (!user) {
        showAlert('Please login first', 'error');
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/games/submit-score`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: user.user_id,
                game_name: gameName,
                score,
                level,
                time_played: timePlayed,
                metadata,
            }),
        });
        const data = await readApiJson(response);

        if (!response.ok) {
            showAlert(data.error || 'Failed to submit score', 'error');
            return;
        }

        const xp = data.xp_earned ?? 0;
        const coins = data.coins_earned ?? 0;
        const rank = data.rank ? `#${data.rank}` : 'N/A';
        const message = data.is_personal_best
            ? `New personal best! Rank ${rank} | +${xp} XP, +${coins} Coins`
            : `Score submitted! Rank ${rank} | +${xp} XP, +${coins} Coins`;
        showAlert(message, 'success');

        if (leaderboardMode === 'global') {
            await loadGlobalLeaderboard();
        } else {
            await loadLeaderboard(gameName);
        }

        if (typeof loadGameStats === 'function') {
            await loadGameStats(user.user_id);
        }
    } catch (error) {
        console.error('Submit score error:', error);
        showAlert('Network error while submitting score', 'error');
    }
}

async function loadLeaderboard(gameName, limit = 100) {
    leaderboardMode = 'game';
    const container = document.getElementById('leaderboardContent');
    if (!container) return;

    try {
        const response = await fetch(`${API_BASE}/games/leaderboard/${encodeURIComponent(gameName)}?limit=${limit}`);
        const data = await readApiJson(response);
        if (!response.ok) {
            throw new Error(data.error || 'Failed to load leaderboard');
        }
        renderLeaderboard(data, `${gameName} Leaderboard`);
    } catch (error) {
        console.error('Leaderboard error:', error);
        container.innerHTML = `<p class="text-muted">Error loading leaderboard: ${escapeHtml(error.message)}</p>`;
    }
}

async function loadGlobalLeaderboard(limit = 100) {
    leaderboardMode = 'global';
    const container = document.getElementById('leaderboardContent');
    if (!container) return;

    try {
        const response = await fetch(`${API_BASE}/games/global-leaderboard?limit=${limit}`);
        const data = await readApiJson(response);
        if (!response.ok) {
            throw new Error(data.error || 'Failed to load global leaderboard');
        }
        renderLeaderboard(data, 'Global Leaderboard (All Games)');
    } catch (error) {
        console.error('Global leaderboard error:', error);
        container.innerHTML = `<p class="text-muted">Error loading global leaderboard: ${escapeHtml(error.message)}</p>`;
    }
}

function renderLeaderboard(data, title) {
    const container = document.getElementById('leaderboardContent');
    if (!container) return;
    const entries = Array.isArray(data.leaderboard) ? data.leaderboard : [];
    const user = getCurrentUser();
    const userId = user ? user.user_id : null;

    if (entries.length === 0) {
        container.innerHTML = `
            <div style="text-align:center; padding:2rem;">
                <h3>${escapeHtml(title)}</h3>
                <p class="text-muted">No scores yet. Play to claim rank #1.</p>
            </div>
        `;
        return;
    }

    container.innerHTML = `
        <h3 style="margin-bottom: 1rem;">${escapeHtml(title)}</h3>
        <table class="leaderboard-table">
            <thead>
                <tr>
                    <th>Rank</th>
                    <th>Player</th>
                    <th>Score</th>
                    <th>Details</th>
                </tr>
            </thead>
            <tbody>
                ${entries.map((entry) => {
                    const isCurrentUser = userId && entry.user_id === userId;
                    const details = leaderboardMode === 'global'
                        ? `${entry.games_played || 0} game(s)`
                        : `Level ${entry.level || 1}`;
                    return `
                        <tr class="leaderboard-entry ${isCurrentUser ? 'current-user' : ''}">
                            <td>#${entry.rank || ''}</td>
                            <td>${escapeHtml(entry.username || 'Unknown')}${isCurrentUser ? ' (You)' : ''}</td>
                            <td>${Number(entry.total_score ?? entry.score ?? 0).toLocaleString()}</td>
                            <td>${escapeHtml(details)}</td>
                        </tr>
                    `;
                }).join('')}
            </tbody>
        </table>
    `;
}

async function loadGameStats(userId) {
    const container = document.getElementById('gameStats');
    if (!container) return;

    try {
        const response = await fetch(`${API_BASE}/game/stats/${userId}`);
        const data = await readApiJson(response);
        if (!response.ok) {
            throw new Error(data.error || 'Failed to load game stats');
        }
        container.innerHTML = `
            <div class="card" style="margin-bottom:1.5rem;">
                <h3>Game Progress</h3>
                <p class="text-muted">
                    Level ${data.current_level || 1} • ${data.total_xp || 0} XP • ${data.dream_coins || 0} Coins
                </p>
            </div>
        `;
    } catch (error) {
        console.error('Game stats error:', error);
        container.innerHTML = `<p class="text-muted">Game stats unavailable.</p>`;
    }
}

async function loadGames() {
    const container = document.getElementById('gamesGrid');
    if (!container) return;

    try {
        const response = await fetch(`${API_BASE}/games`);
        const data = await readApiJson(response);
        const games = response.ok ? (data.games || []) : [];
        const flappyBird = games.find((game) => game.game_name === 'Flappy Bird') || {
            game_name: 'Flappy Bird',
            game_icon: '🐦',
            game_description: 'Navigate through pipes and score points in this classic arcade challenge.',
        };
        const description = flappyBird.game_description || 'Navigate through pipes and score points.';
        container.innerHTML = `
            <div class="game-card" onclick="showGame('Flappy Bird')">
                <div class="game-icon">${escapeHtml(flappyBird.game_icon || '🐦')}</div>
                <h3 class="game-title">Flappy Bird</h3>
                <p class="game-description">${escapeHtml(description)}</p>
                <button class="play-button">Play Now</button>
            </div>
        `;
    } catch (error) {
        console.error('Load games error:', error);
        container.innerHTML = `
            <div class="game-card" onclick="showGame('Flappy Bird')">
                <div class="game-icon">🐦</div>
                <h3 class="game-title">Flappy Bird</h3>
                <p class="game-description">Navigate through pipes and score points in this classic arcade challenge.</p>
                <button class="play-button">Play Now</button>
            </div>
        `;
    }
}

function showGame(gameName) {
    currentGame = gameName;
    const gamesCategory = document.querySelector('.games-category');
    const gamesHeader = document.querySelector('.games-header');
    const gameView = document.getElementById('gameView');

    if (gamesCategory) gamesCategory.style.display = 'none';
    if (gamesHeader) gamesHeader.style.display = 'none';
    if (gameView) gameView.style.display = 'block';
    document.querySelectorAll('.game-container').forEach((el) => {
        el.style.display = 'none';
    });

    if (gameName === 'Flappy Bird') {
        const flappyContainer = document.getElementById('flappybirdContainer');
        if (flappyContainer) {
            flappyContainer.style.display = 'block';
            setTimeout(() => {
                if (typeof initFlappy === 'function') initFlappy();
            }, 100);
        }
    }
}

function showLeaderboard(gameName) {
    const targetGame = gameName || currentGame || 'Flappy Bird';
    currentGame = targetGame;
    const gamesGridParent = document.getElementById('gamesGrid')?.parentElement;
    const gameView = document.getElementById('gameView');
    const leaderboardView = document.getElementById('leaderboardView');
    if (gamesGridParent) gamesGridParent.style.display = 'none';
    if (gameView) gameView.style.display = 'none';
    if (leaderboardView) leaderboardView.style.display = 'block';
    loadLeaderboard(targetGame);
}

function showGlobalLeaderboard() {
    const gamesGridParent = document.getElementById('gamesGrid')?.parentElement;
    const gameView = document.getElementById('gameView');
    const leaderboardView = document.getElementById('leaderboardView');
    if (gamesGridParent) gamesGridParent.style.display = 'none';
    if (gameView) gameView.style.display = 'none';
    if (leaderboardView) leaderboardView.style.display = 'block';
    loadGlobalLeaderboard();
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
}

function refreshLeaderboard() {
    if (leaderboardMode === 'global') {
        loadGlobalLeaderboard();
        return;
    }
    if (currentGame) {
        loadLeaderboard(currentGame);
    }
}