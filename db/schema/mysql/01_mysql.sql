CREATE TABLE `posts` (
  `id` int NOT NULL AUTO_INCREMENT,
  `title` varchar(256) DEFAULT NULL,
  `created` varchar(256) DEFAULT NULL,
  `updated` varchar(256) DEFAULT NULL,
  `link` varchar(1024) DEFAULT NULL,
  `author` varchar(256) DEFAULT NULL,
  `avatar` varchar(1024) DEFAULT NULL,
  `rule` varchar(256) DEFAULT NULL,
  `createdAt` VARCHAR(1024) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=125 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `friends` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(256) DEFAULT NULL,
  `link` varchar(1024) DEFAULT NULL,
  `avatar` varchar(1024) DEFAULT NULL,
  `error` tinyint(1) DEFAULT NULL,
  `createdAt` VARCHAR(1024) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;