<?php
include 'db_config.php';

// --- API И БЭКАП ---
if (isset($_GET['action']) && $_GET['action'] == 'make_backup') {
    $backup_name = 'backup_' . date('Y-m-d_H-i-s') . '.zip';
    $zip = new ZipArchive();
    if ($zip->open($backup_name, ZipArchive::CREATE | ZipArchive::OVERWRITE) === TRUE) {
        $sql_dump = "";
        $tables = ['allowed_cars', 'entry_logs'];
        foreach ($tables as $table) {
            $result = $conn->query("SELECT * FROM $table");
            $num_fields = $result->field_count;
            $sql_dump .= "DROP TABLE IF EXISTS $table;";
            $row2 = $conn->query("SHOW CREATE TABLE $table")->fetch_row();
            $sql_dump .= "\n\n" . $row2[1] . ";\n\n";
            while ($row = $result->fetch_row()) {
                $sql_dump .= "INSERT INTO $table VALUES(";
                for ($j = 0; $j < $num_fields; $j++) {
                    $row[$j] = addslashes($row[$j]);
                    $row[$j] = str_replace("\n", "\\n", $row[$j]);
                    if (isset($row[$j])) { $sql_dump .= '"' . $row[$j] . '"'; } else { $sql_dump .= '""'; }
                    if ($j < ($num_fields - 1)) { $sql_dump .= ','; }
                }
                $sql_dump .= ");\n";
            }
            $sql_dump .= "\n\n\n";
        }
        $zip->addFromString('database_dump.sql', $sql_dump);
        $rootPath = realpath(__DIR__);
        $files = new RecursiveIteratorIterator(new RecursiveCallbackFilterIterator(
            new RecursiveDirectoryIterator($rootPath, RecursiveDirectoryIterator::SKIP_DOTS),
            function ($current) use ($backup_name) { return $current->getFilename() !== $backup_name; }
        ));
        foreach ($files as $name => $file) {
            if (!$file->isDir()) {
                $filePath = $file->getRealPath();
                $relativePath = substr($filePath, strlen($rootPath) + 1);
                $zip->addFile($filePath, $relativePath);
            }
        }
        $zip->close();
        header('Content-Type: application/zip');
        header('Content-Disposition: attachment; filename="' . $backup_name . '"');
        header('Content-Length: ' . filesize($backup_name));
        readfile($backup_name);
        unlink($backup_name);
        exit;
    }
}

if (isset($_GET['action']) && $_GET['action'] == 'get_logs') {
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
    header('Content-Type: application/json');
    echo json_encode(['total_cars' => $total_cars, 'last_activity' => $last_time]);
    exit;
}

// --- ФОРМЫ ---
$alert_msg = "";
$latin_to_rus = ['A'=>'А','B'=>'В','C'=>'С','E'=>'Е','H'=>'Н','K'=>'К','M'=>'М','O'=>'О','P'=>'Р','T'=>'Т','X'=>'Х','Y'=>'У'];

// Добавление записи
if ($_SERVER["REQUEST_METHOD"] == "POST" && isset($_POST['add_plate'])) {
    $plate_number = strtoupper(trim($conn->real_escape_string($_POST['plate_number'])));
    $owner_name = trim($conn->real_escape_string($_POST['owner_name']));
    if (!empty($plate_number)) {
        $plate_number = strtr($plate_number, $latin_to_rus);
        $sql = "INSERT INTO allowed_cars (plate_number, owner_name) VALUES ('$plate_number', '$owner_name') ON DUPLICATE KEY UPDATE owner_name='$owner_name'";
        if ($conn->query($sql) === TRUE) $alert_msg = "success|Номер $plate_number добавлен!";
        else $alert_msg = "danger|Ошибка БД";
    }
}

// Редактирование записи (НОВОЕ)
if ($_SERVER["REQUEST_METHOD"] == "POST" && isset($_POST['edit_plate'])) {
    $id = intval($_POST['id']);
    $plate_number = strtoupper(trim($conn->real_escape_string($_POST['plate_number'])));
    $owner_name = trim($conn->real_escape_string($_POST['owner_name']));
    if (!empty($plate_number) && $id > 0) {
        $plate_number = strtr($plate_number, $latin_to_rus);
        $sql = "UPDATE allowed_cars SET plate_number='$plate_number', owner_name='$owner_name' WHERE id=$id";
        if ($conn->query($sql) === TRUE) $alert_msg = "success|Запись обновлена!";
        else $alert_msg = "danger|Ошибка БД";
    }
}

// Удаление записи
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
    <title>Информационная система КПП</title>
    <link rel="icon" type="image/x-icon" href="favicon.ico">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link rel="stylesheet" href="style.css">
</head>
<body>

<nav class="navbar">
    <div class="brand">
        <img src="favicon.ico" alt="Логотип" style="height: 40px; width: auto; margin-right: 10px;">
        <span>Информационная система КПП</span>
    </div>
    <div class="navbar-actions">
        <a href="?action=make_backup" class="btn-minimal warning"><i class="fas fa-download"></i> Бэкап</a>
        <div class="time-display">
            <div class="clock" id="clock">--:--:--</div>
            <div class="date" id="date">—</div>
        </div>
        <button class="btn-minimal" onclick="location.reload()"><i class="fas fa-redo"></i></button>
    </div>
</nav>

<div class="main">
    <?php if ($alert_msg): 
        $parts = explode('|', $alert_msg); 
        $alertClass = $parts[0] === 'success' ? 'success' : 'danger';
    ?>
        <div class="alert-minimal <?= $alertClass ?>">
            <i class="fas fa-<?= $alertClass==='success'?'check-circle':'exclamation-circle' ?>"></i>
            <span><?= htmlspecialchars($parts[1]) ?></span>
            <button type="button" class="btn-close btn-close-white ms-2" data-bs-dismiss="alert"></button>
        </div>
    <?php endif; ?>

    <div class="card">
        <div class="card-header"><span><i class="fas fa-clock"></i> События</span></div>
        <div class="card-body"><div class="scroll-area" id="logs-container"></div></div>
    </div>

    <div class="d-flex flex-column">
        <div class="card video-card">
            <div class="video-wrapper">
                <img src="http://localhost:5000/video_feed" onerror="this.src='https://placehold.co/1280x720/111/444?text=Нет+сигнала'">
                <div class="video-overlay">
                    <span class="live-indicator">LIVE</span>
                    <span class="text-dim" id="camera-status">● Онлайн</span>
                </div>
            </div>
        </div>
        <div class="stats-bar">
            <div class="stat-item"><div class="stat-value text-accent" id="stat-total">—</div><div class="stat-label">В базе</div></div>
            <div class="stat-item"><div class="stat-value text-success" id="stat-last">—</div><div class="stat-label">Посл. въезд</div></div>
            <div class="stat-item action" onclick="alert('Команда отправлена')"><div class="stat-value"><i class="fas fa-arrow-up"></i></div><div class="stat-label">Открыть</div></div>
        </div>
    </div>

    <div class="card">
        <div class="card-header">
            <span><i class="fas fa-list-check"></i> Доступ</span>
            <button class="add-btn" data-bs-toggle="modal" data-bs-target="#addModal"><i class="fas fa-plus"></i></button>
        </div>
        <div class="card-body">
            <!-- Блок живого поиска (НОВОЕ) -->
            <div class="search-box">
                <i class="fas fa-search"></i>
                <input type="text" id="searchInput" class="form-control" placeholder="Поиск номера или ФИО...">
            </div>
            <div class="scroll-area">
                <table class="plate-table">
                    <tbody id="platesTableBody">
                        <?php
                        $res = $conn->query("SELECT * FROM allowed_cars ORDER BY id DESC");
                        while($res && $r = $res->fetch_assoc()): ?>
                            <tr>
                                <td>
                                    <div class="plate-number"><?= htmlspecialchars($r['plate_number']) ?></div>
                                    <div class="plate-owner"><?= htmlspecialchars($r['owner_name']) ?></div>
                                </td>
                                <td class="plate-action">
                                    <!-- Кнопка редактирования (НОВОЕ) -->
                                    <button type="button" class="btn-icon text-accent" 
                                            onclick="openEditModal(<?= $r['id'] ?>, '<?= htmlspecialchars($r['plate_number']) ?>', '<?= htmlspecialchars($r['owner_name']) ?>')">
                                        <i class="fas fa-edit"></i>
                                    </button>
                                    <a href="?delete_id=<?= $r['id'] ?>" class="btn-icon" onclick="return confirm('Удалить?')"><i class="fas fa-trash-alt"></i></a>
                                </td>
                            </tr>
                        <?php endwhile; ?>
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</div>

<!-- Модальное окно: Добавление -->
<div class="modal fade" id="addModal" tabindex="-1">
    <div class="modal-dialog modal-dialog-centered">
        <form method="POST" class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">Добавить автомобиль</h5>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
                <div class="mb-3">
                    <label class="form-label">Гос. номер</label>
                    <input type="text" name="plate_number" class="form-control text-uppercase" placeholder="А123ВС77" required>
                </div>
                <div class="mb-3">
                    <label class="form-label">Владелец</label>
                    <input type="text" name="owner_name" class="form-control" placeholder="Иванов И.И.">
                </div>
            </div>
            <div class="modal-footer"><button type="submit" name="add_plate" class="btn-save">Сохранить</button></div>
        </form>
    </div>
</div>

<!-- Модальное окно: Редактирование (НОВОЕ) -->
<div class="modal fade" id="editModal" tabindex="-1">
    <div class="modal-dialog modal-dialog-centered">
        <form method="POST" class="modal-content">
            <input type="hidden" name="id" id="edit_id">
            <div class="modal-header">
                <h5 class="modal-title">Редактировать запись</h5>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
                <div class="mb-3">
                    <label class="form-label">Гос. номер</label>
                    <input type="text" name="plate_number" id="edit_plate_number" class="form-control text-uppercase" required>
                </div>
                <div class="mb-3">
                    <label class="form-label">Владелец</label>
                    <input type="text" name="owner_name" id="edit_owner_name" class="form-control">
                </div>
            </div>
            <div class="modal-footer"><button type="submit" name="edit_plate" class="btn-save">Обновить</button></div>
        </form>
    </div>
</div>

<!-- Модальное окно: Просмотр фото / Lightbox (НОВОЕ) -->
<div class="modal fade" id="lightboxModal" tabindex="-1" aria-hidden="true">
    <div class="modal-dialog modal-dialog-centered modal-lg">
        <div class="modal-content lightbox-content">
            <button type="button" class="btn-close btn-close-white lightbox-close" data-bs-dismiss="modal"></button>
            <img id="lightboxImage" src="" alt="Snapshot" class="img-fluid rounded">
        </div>
    </div>
</div>

<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
<script src="script.js"></script>
</body>
</html>