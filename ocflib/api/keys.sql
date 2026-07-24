-- length of key defined by KEY_LENGTH in keys.py
CREATE TABLE IF NOT EXISTS `keys` (
  `key` varchar(32) NOT NULL,
  `user` varchar(255) NOT NULL
  PRIMARY KEY(`key`)
)
