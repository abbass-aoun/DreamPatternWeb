const timelineState = {
    currentDate: new Date(),
    calendarData: {},
};

function formatDateKey(year, monthIndex, day) {
    const mm = String(monthIndex + 1).padStart(2, '0');
    const dd = String(day).padStart(2, '0');
    return `${year}-${mm}-${dd}`;
}

async function loadCalendarData() {
    const user = getCurrentUser();
    if (!user) {
        window.location.href = '/login';
        return;
    }

    const year = timelineState.currentDate.getFullYear();
    const month = timelineState.currentDate.getMonth() + 1;
    const response = await fetch(`${API_BASE}/search/calendar/${user.user_id}?year=${year}&month=${month}`);
    const data = await response.json();
    if (!response.ok) {
        throw new Error(data.error || 'Failed to load calendar');
    }
    timelineState.calendarData = data || {};
}

function renderCalendar() {
    const year = timelineState.currentDate.getFullYear();
    const month = timelineState.currentDate.getMonth();
    const monthLabel = timelineState.currentDate.toLocaleDateString(undefined, {
        month: 'long',
        year: 'numeric',
    });
    document.getElementById('currentMonth').textContent = monthLabel;

    const grid = document.getElementById('calendarGrid');
    const dayHeaders = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
        .map((d) => `<div class="calendar-day-header">${d}</div>`)
        .join('');

    const firstDay = new Date(year, month, 1).getDay();
    const daysInMonth = new Date(year, month + 1, 0).getDate();
    const daysInPrevMonth = new Date(year, month, 0).getDate();
    const today = new Date();

    const cells = [];
    for (let i = firstDay - 1; i >= 0; i--) {
        const dayNum = daysInPrevMonth - i;
        cells.push(`<div class="calendar-day other-month"><div class="day-number">${dayNum}</div></div>`);
    }

    for (let day = 1; day <= daysInMonth; day++) {
        const key = formatDateKey(year, month, day);
        const dreams = timelineState.calendarData[key] || [];
        const isToday =
            today.getFullYear() === year &&
            today.getMonth() === month &&
            today.getDate() === day;

        const classes = ['calendar-day'];
        if (dreams.length > 0) classes.push('has-dreams');
        if (isToday) classes.push('today');

        const indicators = dreams
            .slice(0, 2)
            .map((dream) => {
                const lucidClass = dream.lucid ? 'lucid' : 'normal';
                const icon = dream.lucid ? '⭐' : '🌙';
                return `<div class="dream-indicator ${lucidClass}">${icon} ${dream.dname}</div>`;
            })
            .join('');

        cells.push(`
            <div class="${classes.join(' ')}" onclick="openDayDreams('${key}')">
                <div class="day-number">${day}</div>
                <div class="day-dreams">
                    ${indicators}
                    ${dreams.length > 2 ? `<div class="dream-indicator normal">+${dreams.length - 2} more</div>` : ''}
                </div>
            </div>
        `);
    }

    const totalCells = firstDay + daysInMonth;
    const remaining = (7 - (totalCells % 7)) % 7;
    for (let i = 1; i <= remaining; i++) {
        cells.push(`<div class="calendar-day other-month"><div class="day-number">${i}</div></div>`);
    }

    grid.innerHTML = `${dayHeaders}${cells.join('')}`;
}

function openDayDreams(dateKey) {
    const dreams = timelineState.calendarData[dateKey] || [];
    if (dreams.length === 0) return;

    document.getElementById('modalDate').textContent = new Date(dateKey).toLocaleDateString(undefined, {
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric',
    });

    document.getElementById('modalDreams').innerHTML = dreams
        .map(
            (dream) => `
        <div class="dream-item" onclick="window.location.href='/dream-detail?id=${dream.dream_id}'">
            <h4 style="margin:0 0 .5rem 0;">${dream.dname}</h4>
            <p class="text-muted" style="margin:0;">
                Intensity: ${dream.intensity}/10 ${dream.lucid ? ' • Lucid ⭐' : ''}
            </p>
            ${dream.emotions ? `<p style="margin:.5rem 0 0 0; font-size:.9rem;">Emotions: ${dream.emotions}</p>` : ''}
        </div>`
        )
        .join('');

    document.getElementById('dreamModal').classList.add('active');
}

function closeModal() {
    document.getElementById('dreamModal').classList.remove('active');
}

async function refreshTimeline() {
    try {
        await loadCalendarData();
        renderCalendar();
    } catch (error) {
        console.error('Timeline error:', error);
        showAlert(error.message || 'Failed to load timeline', 'error');
    }
}

async function changeMonth(offset) {
    timelineState.currentDate.setMonth(timelineState.currentDate.getMonth() + offset);
    await refreshTimeline();
}

async function goToToday() {
    timelineState.currentDate = new Date();
    await refreshTimeline();
}

document.addEventListener('DOMContentLoaded', async () => {
    const user = checkAuth();
    if (!user) return;
    await refreshTimeline();
});
