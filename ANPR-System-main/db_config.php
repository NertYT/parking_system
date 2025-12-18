<?php
// Настройки подключения к базе данных MySQL
$servername = "localhost";
$username = "root";       // Ваш логин phpMyAdmin
$password = "";           // Ваш пароль phpMyAdmin
$dbname = "parking_system"; // Имя БД, которое вы создали

// Создание соединения
$conn = new mysqli($servername, $username, $password, $dbname);

// Проверка соединения
if ($conn->connect_error) {
    die("Ошибка подключения к базе данных: " . $conn->connect_error);
}
?>