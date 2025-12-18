-- phpMyAdmin SQL Dump
-- version 5.1.3-3.red80
-- https://www.phpmyadmin.net/
--
-- Хост: localhost
-- Время создания: Дек 16 2025 г., 05:45
-- Версия сервера: 10.11.11-MariaDB
-- Версия PHP: 8.1.32

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- База данных: `parking_system`
--

-- --------------------------------------------------------

--
-- Структура таблицы `allowed_cars`
--

CREATE TABLE `allowed_cars` (
  `id` int(11) NOT NULL,
  `plate_number` varchar(20) NOT NULL,
  `owner_name` varchar(100) DEFAULT NULL,
  `is_active` tinyint(1) DEFAULT 1,
  `created_at` timestamp NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Дамп данных таблицы `allowed_cars`
--

INSERT INTO `allowed_cars` (`id`, `plate_number`, `owner_name`, `is_active`, `created_at`) VALUES
(10, 'А510ОВ142', 'Кирюха', 1, '2025-12-16 05:12:01'),
(14, 'С532НР142', 'Админ', 1, '2025-12-16 05:23:19');

-- --------------------------------------------------------

--
-- Структура таблицы `entry_logs`
--

CREATE TABLE `entry_logs` (
  `id` int(11) NOT NULL,
  `plate_number` varchar(20) DEFAULT NULL,
  `status` enum('access_granted','access_denied') NOT NULL,
  `snapshot_path` varchar(255) DEFAULT NULL,
  `event_time` timestamp NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Дамп данных таблицы `entry_logs`
--

INSERT INTO `entry_logs` (`id`, `plate_number`, `status`, `snapshot_path`, `event_time`) VALUES
(390, 'B510OB142', 'access_denied', 'snapshots/B510OB142_20251216_122201_886.jpg', '2025-12-16 05:22:01'),
(391, 'A510OB142', 'access_granted', 'snapshots/A510OB142_20251216_122203_781.jpg', '2025-12-16 05:22:03'),
(392, 'H510OB14', 'access_denied', 'snapshots/H510OB14_20251216_122206_189.jpg', '2025-12-16 05:22:06'),
(393, 'A510OB142', 'access_granted', 'snapshots/A510OB142_20251216_122206_346.jpg', '2025-12-16 05:22:06'),
(394, 'H510OB14', 'access_denied', 'snapshots/H510OB14_20251216_122206_447.jpg', '2025-12-16 05:22:06'),
(395, 'B510OB142', 'access_denied', 'snapshots/B510OB142_20251216_122208_250.jpg', '2025-12-16 05:22:08'),
(396, 'A510OB142', 'access_granted', 'snapshots/A510OB142_20251216_122208_944.jpg', '2025-12-16 05:22:08'),
(397, 'A510OB14', 'access_denied', 'snapshots/A510OB14_20251216_122209_409.jpg', '2025-12-16 05:22:09'),
(398, 'A510OB142', 'access_granted', 'snapshots/A510OB142_20251216_122209_866.jpg', '2025-12-16 05:22:09'),
(399, 'E510OB142', 'access_denied', 'snapshots/E510OB142_20251216_122210_455.jpg', '2025-12-16 05:22:10'),
(400, 'A510OB142', 'access_granted', 'snapshots/A510OB142_20251216_122210_548.jpg', '2025-12-16 05:22:10'),
(401, 'C510OB142', 'access_denied', 'snapshots/C510OB142_20251216_122210_701.jpg', '2025-12-16 05:22:10'),
(402, 'E510OB142', 'access_denied', 'snapshots/E510OB142_20251216_122210_767.jpg', '2025-12-16 05:22:10'),
(403, 'H510OB142', 'access_denied', 'snapshots/H510OB142_20251216_122210_868.jpg', '2025-12-16 05:22:10'),
(404, 'E510OB142', 'access_denied', 'snapshots/E510OB142_20251216_122210_932.jpg', '2025-12-16 05:22:10'),
(405, 'H510OB142', 'access_denied', 'snapshots/H510OB142_20251216_122210_997.jpg', '2025-12-16 05:22:11'),
(406, 'A510OB142', 'access_granted', 'snapshots/A510OB142_20251216_122211_101.jpg', '2025-12-16 05:22:11'),
(407, 'C510OB142', 'access_denied', 'snapshots/C510OB142_20251216_122211_446.jpg', '2025-12-16 05:22:11'),
(408, 'A510OB142', 'access_granted', 'snapshots/A510OB142_20251216_122211_511.jpg', '2025-12-16 05:22:11'),
(409, 'A510OB14', 'access_denied', 'snapshots/A510OB14_20251216_122213_180.jpg', '2025-12-16 05:22:13'),
(410, 'A510OB142', 'access_granted', 'snapshots/A510OB142_20251216_122213_556.jpg', '2025-12-16 05:22:13'),
(411, 'A510OB14', 'access_denied', 'snapshots/A510OB14_20251216_122214_987.jpg', '2025-12-16 05:22:15'),
(412, 'A510OB142', 'access_granted', 'snapshots/A510OB142_20251216_122215_597.jpg', '2025-12-16 05:22:15'),
(413, 'C532HB192', 'access_denied', 'snapshots/C532HB192_20251216_122424_956.jpg', '2025-12-16 05:24:25'),
(414, 'C532HB162', 'access_denied', 'snapshots/C532HB162_20251216_122425_381.jpg', '2025-12-16 05:24:25'),
(415, 'C7087', 'access_denied', 'snapshots/C7087_20251216_122431_155.jpg', '2025-12-16 05:24:31'),
(416, 'C77838', 'access_denied', 'snapshots/C77838_20251216_122431_896.jpg', '2025-12-16 05:24:31'),
(417, 'C582HB14', 'access_denied', 'snapshots/C582HB14_20251216_122432_768.jpg', '2025-12-16 05:24:32'),
(418, 'C582HB112', 'access_denied', 'snapshots/C582HB112_20251216_122433_079.jpg', '2025-12-16 05:24:33'),
(419, 'C532HB192', 'access_denied', 'snapshots/C532HB192_20251216_122433_394.jpg', '2025-12-16 05:24:33'),
(420, 'C532HP142', 'access_granted', 'snapshots/C532HP142_20251216_122433_733.jpg', '2025-12-16 05:24:33'),
(421, 'A510OB142', 'access_granted', 'snapshots/A510OB142_20251216_123224_893.jpg', '2025-12-16 05:32:24'),
(422, 'C582HP112', 'access_denied', 'snapshots/C582HP112_20251216_123330_084.jpg', '2025-12-16 05:33:30'),
(423, 'C532HP13', 'access_denied', 'snapshots/C532HP13_20251216_123338_140.jpg', '2025-12-16 05:33:38'),
(424, 'C582HP16', 'access_denied', 'snapshots/C582HP16_20251216_123339_224.jpg', '2025-12-16 05:33:39'),
(425, 'C582HP1', 'access_denied', 'snapshots/C582HP1_20251216_123414_171.jpg', '2025-12-16 05:34:14'),
(426, 'C582HP16', 'access_denied', 'snapshots/C582HP16_20251216_123414_497.jpg', '2025-12-16 05:34:14'),
(427, 'C532HP14', 'access_denied', 'snapshots/C532HP14_20251216_123421_028.jpg', '2025-12-16 05:34:21'),
(428, 'C582HP16', 'access_denied', 'snapshots/C582HP16_20251216_123421_103.jpg', '2025-12-16 05:34:21'),
(429, 'C582HP14', 'access_denied', 'snapshots/C582HP14_20251216_123421_191.jpg', '2025-12-16 05:34:21'),
(430, 'C532HP14', 'access_denied', 'snapshots/C532HP14_20251216_123421_324.jpg', '2025-12-16 05:34:21'),
(431, 'C582HP14', 'access_denied', 'snapshots/C582HP14_20251216_123421_524.jpg', '2025-12-16 05:34:21'),
(432, 'E832HC14', 'access_denied', 'snapshots/E832HC14_20251216_123421_789.jpg', '2025-12-16 05:34:21'),
(433, 'E532HC14', 'access_denied', 'snapshots/E532HC14_20251216_123422_122.jpg', '2025-12-16 05:34:22'),
(434, 'E832HC14', 'access_denied', 'snapshots/E832HC14_20251216_123422_200.jpg', '2025-12-16 05:34:22'),
(435, 'E532HC14', 'access_denied', 'snapshots/E532HC14_20251216_123422_265.jpg', '2025-12-16 05:34:22'),
(436, 'C582HP14', 'access_denied', 'snapshots/C582HP14_20251216_123422_796.jpg', '2025-12-16 05:34:22'),
(437, 'C532HP8', 'access_denied', 'snapshots/C532HP8_20251216_123423_194.jpg', '2025-12-16 05:34:23'),
(438, 'C582HP14', 'access_denied', 'snapshots/C582HP14_20251216_123423_358.jpg', '2025-12-16 05:34:23'),
(439, 'C523XH314', 'access_denied', 'snapshots/C523XH314_20251216_123424_061.jpg', '2025-12-16 05:34:24'),
(440, 'C582HP14', 'access_denied', 'snapshots/C582HP14_20251216_123424_161.jpg', '2025-12-16 05:34:24'),
(441, 'C582HP16', 'access_denied', 'snapshots/C582HP16_20251216_123431_518.jpg', '2025-12-16 05:34:31'),
(442, 'C532HC14', 'access_denied', 'snapshots/C532HC14_20251216_123432_921.jpg', '2025-12-16 05:34:32'),
(443, 'C832HC14', 'access_denied', 'snapshots/C832HC14_20251216_123433_441.jpg', '2025-12-16 05:34:33'),
(444, 'C582HP16', 'access_denied', 'snapshots/C582HP16_20251216_123433_849.jpg', '2025-12-16 05:34:33'),
(445, 'E532HC14', 'access_denied', 'snapshots/E532HC14_20251216_123434_566.jpg', '2025-12-16 05:34:34'),
(446, 'C587HP14', 'access_denied', 'snapshots/C587HP14_20251216_123434_713.jpg', '2025-12-16 05:34:34'),
(447, 'C537HP14', 'access_denied', 'snapshots/C537HP14_20251216_123434_873.jpg', '2025-12-16 05:34:34'),
(448, 'C587HP14', 'access_denied', 'snapshots/C587HP14_20251216_123434_939.jpg', '2025-12-16 05:34:34'),
(449, 'C582HP1', 'access_denied', 'snapshots/C582HP1_20251216_123435_064.jpg', '2025-12-16 05:34:35'),
(450, 'C532HP14', 'access_denied', 'snapshots/C532HP14_20251216_123435_133.jpg', '2025-12-16 05:34:35'),
(451, 'C532HC14', 'access_denied', 'snapshots/C532HC14_20251216_123435_655.jpg', '2025-12-16 05:34:35'),
(452, 'C582YHP14', 'access_denied', 'snapshots/C582YHP14_20251216_123435_832.jpg', '2025-12-16 05:34:35'),
(453, 'C532HC14', 'access_denied', 'snapshots/C532HC14_20251216_123435_964.jpg', '2025-12-16 05:34:35'),
(454, 'C582HP14', 'access_denied', 'snapshots/C582HP14_20251216_123436_063.jpg', '2025-12-16 05:34:36'),
(455, 'C582YHP14', 'access_denied', 'snapshots/C582YHP14_20251216_123436_126.jpg', '2025-12-16 05:34:36'),
(456, 'C582HP14', 'access_denied', 'snapshots/C582HP14_20251216_123436_392.jpg', '2025-12-16 05:34:36'),
(457, 'C582HB19', 'access_denied', 'snapshots/C582HB19_20251216_123437_209.jpg', '2025-12-16 05:34:37'),
(458, 'E532H314', 'access_denied', 'snapshots/E532H314_20251216_123437_724.jpg', '2025-12-16 05:34:37'),
(459, 'E532HC14', 'access_denied', 'snapshots/E532HC14_20251216_123437_863.jpg', '2025-12-16 05:34:37'),
(460, 'C532CC74', 'access_denied', 'snapshots/C532CC74_20251216_123438_839.jpg', '2025-12-16 05:34:38'),
(461, 'C582HP1', 'access_denied', 'snapshots/C582HP1_20251216_123439_116.jpg', '2025-12-16 05:34:39'),
(462, 'C582HP14', 'access_denied', 'snapshots/C582HP14_20251216_123439_598.jpg', '2025-12-16 05:34:39'),
(463, 'C532HP142', 'access_granted', 'snapshots/C532HP142_20251216_123525_069.jpg', '2025-12-16 05:35:25'),
(464, 'C532HP142', 'access_granted', 'snapshots/C532HP142_20251216_123554_412.jpg', '2025-12-16 05:35:54'),
(465, 'M284EH67', 'access_denied', 'snapshots/M284EH67_20251216_123617_902.jpg', '2025-12-16 05:36:17'),
(466, 'H510OB142', 'access_denied', 'snapshots/H510OB142_20251216_123824_873.jpg', '2025-12-16 05:38:24'),
(467, 'E510OB142', 'access_denied', 'snapshots/E510OB142_20251216_123825_315.jpg', '2025-12-16 05:38:25'),
(468, 'B510OB142', 'access_denied', 'snapshots/B510OB142_20251216_123832_181.jpg', '2025-12-16 05:38:32'),
(469, 'A510OB142', 'access_granted', 'snapshots/A510OB142_20251216_123832_615.jpg', '2025-12-16 05:38:32'),
(470, 'H510OB142', 'access_denied', 'snapshots/H510OB142_20251216_123833_280.jpg', '2025-12-16 05:38:33'),
(471, 'E510OB142', 'access_denied', 'snapshots/E510OB142_20251216_123833_448.jpg', '2025-12-16 05:38:33'),
(472, 'E510OB142', 'access_denied', 'snapshots/E510OB142_20251216_124303_753.jpg', '2025-12-16 05:43:03'),
(473, 'H510OB142', 'access_denied', 'snapshots/H510OB142_20251216_124303_873.jpg', '2025-12-16 05:43:03'),
(474, 'E510OB142', 'access_denied', 'snapshots/E510OB142_20251216_124306_891.jpg', '2025-12-16 05:43:06'),
(475, 'H510OB142', 'access_denied', 'snapshots/H510OB142_20251216_124307_203.jpg', '2025-12-16 05:43:07'),
(476, 'A510OB142', 'access_granted', 'snapshots/A510OB142_20251216_124307_341.jpg', '2025-12-16 05:43:07'),
(477, 'H510OB142', 'access_denied', 'snapshots/H510OB142_20251216_124307_409.jpg', '2025-12-16 05:43:07'),
(478, 'A510OB142', 'access_granted', 'snapshots/A510OB142_20251216_124307_481.jpg', '2025-12-16 05:43:07'),
(479, 'H510OB142', 'access_denied', 'snapshots/H510OB142_20251216_124307_710.jpg', '2025-12-16 05:43:07'),
(480, 'A510OB142', 'access_granted', 'snapshots/A510OB142_20251216_124307_790.jpg', '2025-12-16 05:43:07'),
(481, 'H510OB142', 'access_denied', 'snapshots/H510OB142_20251216_124308_063.jpg', '2025-12-16 05:43:08'),
(482, 'E510OB142', 'access_denied', 'snapshots/E510OB142_20251216_124308_682.jpg', '2025-12-16 05:43:08');

--
-- Индексы сохранённых таблиц
--

--
-- Индексы таблицы `allowed_cars`
--
ALTER TABLE `allowed_cars`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `plate_number` (`plate_number`);

--
-- Индексы таблицы `entry_logs`
--
ALTER TABLE `entry_logs`
  ADD PRIMARY KEY (`id`);

--
-- AUTO_INCREMENT для сохранённых таблиц
--

--
-- AUTO_INCREMENT для таблицы `allowed_cars`
--
ALTER TABLE `allowed_cars`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=28;

--
-- AUTO_INCREMENT для таблицы `entry_logs`
--
ALTER TABLE `entry_logs`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=483;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
