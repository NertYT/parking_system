// Clock
const updateTime = () => {
    const now = new Date();
    const clockEl = document.getElementById('clock');
    const dateEl = document.getElementById('date');
    
    if(clockEl) clockEl.textContent = now.toLocaleTimeString('ru-RU', {hour:'2-digit', minute:'2-digit', second:'2-digit'});
    if(dateEl) dateEl.textContent = now.toLocaleDateString('ru-RU', {weekday:'short', day:'numeric', month:'short'});
};

// Data Fetch (Stats and Logs)
const updateData = async () => {
    try {
        // Stats
        const statsRes = await fetch('index.php?action=get_stats');
        const stats = await statsRes.json();
        document.getElementById('stat-total').textContent = stats.total_cars;
        document.getElementById('stat-last').textContent = stats.last_activity;
        
        // Logs
        const logsRes = await fetch('index.php?action=get_logs');
        const logs = await logsRes.json();
        const container = document.getElementById('logs-container');
        
        if (!logs || !logs.length) {
            container.innerHTML = `<div class="empty-state"><i class="fas fa-inbox"></i><div>Нет событий</div></div>`;
        } else {
            container.innerHTML = logs.map(l => {
                const ok = l.status === 'access_granted';
                const img = l.snapshot_path ? l.snapshot_path : 'https://placehold.co/100x60/222/666?text=—';
                const time = l.event_time ? l.event_time.split(' ')[1].substring(0,5) : '--:--';
                return `
                <div class="log-item">
                    <div class="log-thumb"><img src="${img}" alt="" onerror="this.src='https://placehold.co/100x60/222/666?text=—'"></div>
                    <div class="log-content">
                        <div class="log-plate">${l.plate_number || '—'}</div>
                        <div class="log-meta">
                            <span>${time}</span>
                            <span class="log-status ${ok ? 'ok' : 'deny'}">
                                <i class="fas fa-${ok ? 'check' : 'times'}"></i>
                                ${ok ? 'Доступ' : 'Отказ'}
                            </span>
                        </div>
                    </div>
                </div>`;
            }).join('');
        }
        
        // Camera status check
        const cam = document.querySelector('.video-wrapper img');
        const statusEl = document.getElementById('camera-status');
        if (cam && cam.complete && cam.naturalHeight !== 0) {
            statusEl.textContent = '● Онлайн';
            statusEl.className = 'text-success';
        } else {
            statusEl.textContent = '○ Офлайн';
            statusEl.className = 'text-dim';
        }
                
    } catch (e) {
        console.error('Update error:', e);
    }
};

// Initialization
document.addEventListener('DOMContentLoaded', () => {
    setInterval(updateTime, 1000);
    updateTime();

    setInterval(updateData, 3000);
    updateData();

    // Auto-hide alerts
    document.querySelectorAll('.alert-minimal').forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 4000);
    });

    // Prevent form resubmission on refresh
    if (window.history.replaceState) {
        window.history.replaceState(null, null, window.location.href);
    }
});