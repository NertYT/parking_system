<?php
include 'db_config.php';

// --- API ---
if (isset($_GET['action']) && $_GET['action'] == 'get_logs') {
    // Берем последние 15 записей
    $sql = "SELECT plate_number, status, event_time, snapshot_path FROM entry_logs ORDER BY event_time DESC LIMIT 15";
    $result = $conn->query($sql);
    $logs = [];
    while($row = $result->fetch_assoc()) $logs[] = $row;
    header('Content-Type: application/json');
    echo json_encode($logs);
    exit;
}

if (isset($_GET['action']) && $_GET['action'] == 'get_stats') {
    $total_cars = $conn->query("SELECT COUNT(*) as c FROM allowed_cars")->fetch_assoc()['c'];
    $last_log = $conn->query("SELECT event_time FROM entry_logs ORDER BY event_time DESC LIMIT 1")->fetch_assoc();
    $last_time = $last_log ? date('H:i', strtotime($last_log['event_time'])) : "--:--";
    echo json_encode(['total_cars' => $total_cars, 'last_activity' => $last_time]);
    exit;
}

// --- ОБРАБОТКА ФОРМ ---
$alert_msg = "";
if ($_SERVER["REQUEST_METHOD"] == "POST" && isset($_POST['add_plate'])) {
    $plate_number = strtoupper(trim($conn->real_escape_string($_POST['plate_number'])));
    $owner_name = trim($conn->real_escape_string($_POST['owner_name']));
    if (!empty($plate_number)) {
        $latin_to_rus = ['A'=>'А','B'=>'В','C'=>'С','E'=>'Е','H'=>'Н','K'=>'К','M'=>'М','O'=>'О','P'=>'Р','T'=>'Т','X'=>'Х','Y'=>'У'];
        $plate_number = strtr($plate_number, $latin_to_rus);
        $sql = "INSERT INTO allowed_cars (plate_number, owner_name) VALUES ('$plate_number', '$owner_name') ON DUPLICATE KEY UPDATE owner_name='$owner_name'";
        if ($conn->query($sql) === TRUE) $alert_msg = "success|Номер $plate_number добавлен!";
        else $alert_msg = "danger|Ошибка БД";
    }
}
if (isset($_GET['delete_id'])) {
    $conn->query("DELETE FROM allowed_cars WHERE id=".intval($_GET['delete_id']));
    header("Location: index.php"); exit;
}
?>

<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Smart Barrier Control</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        :root {
            --bg-dark: #121212;
            --bg-card: #1e1e1e;
            --border-color: #333;
            --accent-green: #00c853;
            --accent-red: #ff3d00;
            --text-main: #e0e0e0;
        }
        body { background-color: var(--bg-dark); color: var(--text-main); font-family: 'Segoe UI', Roboto, sans-serif; overflow: hidden; height: 100vh; }
        
        /* Layout Structure */
        .main-container { height: calc(100vh - 60px); padding-top: 15px; }
        .h-custom-scroll { height: calc(100% - 50px); overflow-y: auto; padding-right: 5px; }
        
        /* Scrollbar */
        ::-webkit-scrollbar { width: 6px; }
        ::-webkit-scrollbar-track { background: var(--bg-dark); }
        ::-webkit-scrollbar-thumb { background: #555; border-radius: 3px; }
        ::-webkit-scrollbar-thumb:hover { background: #777; }

        /* Navbar */
        .navbar { background-color: #1a1a1a; border-bottom: 1px solid var(--border-color); height: 60px; }
        .brand-icon { color: var(--accent-green); }

        /* Cards */
        .custom-card { 
            background-color: var(--bg-card); 
            border: 1px solid var(--border-color); 
            border-radius: 12px; 
            height: 100%; 
            display: flex; flex-direction: column;
            box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        }
        .card-header-custom {
            padding: 15px;
            border-bottom: 1px solid var(--border-color);
            font-weight: 600;
            font-size: 1.1rem;
            display: flex; justify-content: space-between; align-items: center;
        }

        /* Log List Items */
        .log-item {
            display: flex;
            align-items: center;
            padding: 12px;
            border-bottom: 1px solid #2a2a2a;
            transition: background 0.2s;
        }
        .log-item:hover { background-color: #2a2a2a; }
        .log-img-wrapper {
            width: 60px; height: 40px;
            border-radius: 6px;
            overflow: hidden;
            margin-right: 12px;
            border: 1px solid #444;
            cursor: pointer;
            position: relative;
        }
        .log-img-wrapper img { width: 100%; height: 100%; object-fit: cover; transition: transform 0.3s; }
        .log-img-wrapper:hover img { transform: scale(1.1); }
        .log-img-wrapper::after {
            content: '\f00e'; font-family: "Font Awesome 6 Free"; font-weight: 900;
            position: absolute; top:0; left:0; width:100%; height:100%;
            background: rgba(0,0,0,0.5); color: #fff;
            display: flex; justify-content: center; align-items: center;
            opacity: 0; transition: opacity 0.2s; font-size: 12px;
        }
        .log-img-wrapper:hover::after { opacity: 1; }

        .log-info { flex-grow: 1; }
        .log-plate { font-weight: 700; font-size: 1.1rem; letter-spacing: 1px; color: #fff; display: block; }
        .log-time { font-size: 0.8rem; color: #888; }
        .log-status-indicator { width: 4px; height: 30px; border-radius: 2px; margin-left: 10px; }
        .status-ok { background-color: var(--accent-green); box-shadow: 0 0 8px rgba(0,200,83,0.4); }
        .status-bad { background-color: var(--accent-red); box-shadow: 0 0 8px rgba(255,61,0,0.4); }

        /* Video Feed */
        .video-wrapper {
            width: 100%;
            padding-bottom: 56.25%; /* 16:9 */
            background: #000;
            position: relative;
            border-radius: 8px;
            overflow: hidden;
            border: 1px solid #444;
        }
        .video-wrapper img { position: absolute; top: 0; left: 0; width: 100%; height: 100%; object-fit: contain; }

        /* Stats & Controls */
        .stat-box {
            background: #252525; border-radius: 10px; padding: 15px; text-align: center;
            border: 1px solid #333; margin-top: 15px;
        }
        .stat-value { font-size: 1.8rem; font-weight: bold; color: #fff; }
        .stat-label { font-size: 0.85rem; color: #aaa; text-transform: uppercase; letter-spacing: 1px; }

        /* Whitelist Table */
        .table-custom { width: 100%; border-collapse: collapse; }
        .table-custom td { padding: 10px; border-bottom: 1px solid #2a2a2a; color: #ccc; }
        .table-custom tr:last-child td { border-bottom: none; }
        .table-custom .plate-cell { font-weight: bold; color: #fff; }
        .btn-del { color: #666; transition: 0.2s; cursor: pointer; }
        .btn-del:hover { color: var(--accent-red); }
    </style>
</head>
<body>

<!-- Navbar -->
<nav class="navbar px-4">
    <div class="d-flex align-items-center">
        <i class="fas fa-video fa-lg brand-icon me-3"></i>
        <h5 class="mb-0 text-white">Smart <span class="fw-light">Barrier</span></h5>
    </div>
    <div class="d-flex align-items-center text-white">
        <div class="me-4 text-end">
            <div id="clock" class="fw-bold" style="font-size: 1.1rem;">--:--:--</div>
            <div id="date" style="font-size: 0.8rem; color: #888;">Загрузка...</div>
        </div>
        <button class="btn btn-outline-light btn-sm" onclick="location.reload()"><i class="fas fa-sync-alt"></i></button>
    </div>
</nav>

<div class="container-fluid main-container px-4">
    <?php if ($alert_msg): $parts = explode('|', $alert_msg); ?>
        <div class="alert alert-<?= $parts[0] ?> alert-dismissible fade show absolute-alert" style="position:absolute; top: 70px; right: 20px; z-index: 100;">
            <?= $parts[1] ?> <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    <?php endif; ?>

    <div class="row g-4 h-100">
        
        <!-- COLUMN 1: LIVE JOURNAL (С Фото) -->
        <div class="col-lg-3 h-100">
            <div class="custom-card">
                <div class="card-header-custom">
                    <span><i class="fas fa-history me-2 text-primary"></i>События</span>
                    <span class="badge bg-dark border border-secondary">Live</span>
                </div>
                <div class="h-custom-scroll" id="logs-container">
                    <!-- JS Injects logs here -->
                </div>
            </div>
        </div>

        <!-- COLUMN 2: CAMERA & STATS -->
        <div class="col-lg-6 h-100 d-flex flex-column">
            <!-- Video -->
            <div class="custom-card p-2 flex-grow-0">
                <div class="video-wrapper">
                    <img src="http://localhost:5000/video_feed" onerror="this.src='https://placehold.co/800x450/000/FFF?text=Нет+сигнала+с+сервера+Python'">
                </div>
            </div>

            <!-- Stats Row -->
            <div class="row mt-auto">
                <div class="col-4">
                    <div class="stat-box">
                        <div class="stat-value text-primary" id="stat-total">-</div>
                        <div class="stat-label">В базе</div>
                    </div>
                </div>
                <div class="col-4">
                    <div class="stat-box">
                        <div class="stat-value text-warning" id="stat-last">-</div>
                        <div class="stat-label">Посл. въезд</div>
                    </div>
                </div>
                <div class="col-4">
                    <div class="stat-box" style="cursor: pointer; border-color: #444;" onclick="alert('Команда на открытие отправлена!')">
                        <div class="stat-value text-success"><i class="fas fa-arrow-up"></i></div>
                        <div class="stat-label">Открыть</div>
                    </div>
                </div>
            </div>
        </div>

        <!-- COLUMN 3: WHITELIST -->
        <div class="col-lg-3 h-100">
            <div class="custom-card">
                <div class="card-header-custom">
                    <span><i class="fas fa-car me-2 text-warning"></i>Белый список</span>
                    <button class="btn btn-sm btn-primary rounded-circle" style="width: 30px; height: 30px;" data-bs-toggle="modal" data-bs-target="#addModal"><i class="fas fa-plus"></i></button>
                </div>
                <div class="h-custom-scroll">
                    <table class="table-custom">
                        <tbody>
                            <?php
                            $res = $conn->query("SELECT * FROM allowed_cars ORDER BY id DESC");
                            while($r = $res->fetch_assoc()): ?>
                                <tr>
                                    <td class="plate-cell"><?= $r['plate_number'] ?></td>
                                    <td class="small text-muted"><?= $r['owner_name'] ?></td>
                                    <td class="text-end"><a href="?delete_id=<?= $r['id'] ?>" class="btn-del" onclick="return confirm('Удалить?')"><i class="fas fa-trash"></i></a></td>
                                </tr>
                            <?php endwhile; ?>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>
</div>

<!-- Modal Add -->
<div class="modal fade" id="addModal" tabindex="-1">
    <div class="modal-dialog modal-dialog-centered">
        <form method="POST" class="modal-content bg-dark text-white border-secondary">
            <div class="modal-header border-secondary">
                <h5 class="modal-title">Добавить авто</h5>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
                <div class="mb-3">
                    <label>Гос. номер</label>
                    <input type="text" name="plate_number" class="form-control bg-secondary text-white border-0 form-control-lg text-uppercase text-center" placeholder="A 000 AA 77" required>
                </div>
                <div class="mb-3">
                    <label>Владелец</label>
                    <input type="text" name="owner_name" class="form-control bg-secondary text-white border-0" placeholder="Комментарий">
                </div>
            </div>
            <div class="modal-footer border-secondary">
                <button type="submit" name="add_plate" class="btn btn-success w-100">Сохранить</button>
            </div>
        </form>
    </div>
</div>

<!-- Modal Photo Preview -->
<div class="modal fade" id="photoModal" tabindex="-1">
    <div class="modal-dialog modal-dialog-centered modal-lg">
        <div class="modal-content bg-dark border-secondary">
            <div class="modal-header border-secondary py-2">
                <h6 class="modal-title text-white" id="photoModalLabel">Фото фиксации</h6>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body p-0 text-center bg-black">
                <img id="modalImage" src="" style="max-width: 100%; max-height: 80vh;">
            </div>
        </div>
    </div>
</div>

<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
<script>
    // Clock
    setInterval(() => {
        const now = new Date();
        document.getElementById('clock').innerText = now.toLocaleTimeString();
        document.getElementById('date').innerText = now.toLocaleDateString();
    }, 1000);

    // Show Photo Modal
    function showPhoto(url, plate) {
        document.getElementById('modalImage').src = url;
        document.getElementById('photoModalLabel').innerText = 'Фото фиксации: ' + plate;
        new bootstrap.Modal(document.getElementById('photoModal')).show();
    }

    // Update Dashboard
    async function updateData() {
        try {
            // Stats
            let s = await (await fetch('index.php?action=get_stats')).json();
            document.getElementById('stat-total').innerText = s.total_cars;
            document.getElementById('stat-last').innerText = s.last_activity;

            // Logs
            let logs = await (await fetch('index.php?action=get_logs')).json();
            let html = '';
            
            if(logs.length === 0) {
                document.getElementById('logs-container').innerHTML = '<div class="text-center text-muted mt-5"><i class="fas fa-ghost mb-2"></i><br>Нет записей</div>';
                return;
            }

            logs.forEach(l => {
                let isOk = l.status === 'access_granted';
                let colorClass = isOk ? 'status-ok' : 'status-bad';
                let imgPath = l.snapshot_path ? l.snapshot_path : 'https://placehold.co/100x60/333/666?text=No+Img';
                
                // Форматируем время (только часы и минуты)
                let time = l.event_time.split(' ')[1].substring(0, 5);
                
                html += `
                    <div class="log-item">
                        <div class="log-img-wrapper" onclick="showPhoto('${imgPath}', '${l.plate_number}')">
                            <img src="${imgPath}" alt="snap">
                        </div>
                        <div class="log-info">
                            <span class="log-plate">${l.plate_number}</span>
                            <span class="log-time">${time} • ${isOk ? 'Доступ' : 'Отказ'}</span>
                        </div>
                        <div class="log-status-indicator ${colorClass}"></div>
                    </div>
                `;
            });
            document.getElementById('logs-container').innerHTML = html;

        } catch(e) { console.error(e); }
    }

    setInterval(updateData, 2000);
    updateData();
</script>
</body>
</html>