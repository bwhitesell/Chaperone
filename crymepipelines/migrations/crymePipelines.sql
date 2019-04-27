-- Build Script for the crymepipelines database:

CREATE TABLE IF NOT EXISTS dataset (
  id INT AUTO_INCREMENT,
  latitude FLOAT(53) NOT NULL,
  longitude FLOAT(53) NOT NULL,
  timestamp DATETIME NOT NULL,
  estimate VARCHAR(255),
  model_id VARCHAR(255),
  lat_bb INT NOT NULL,
  lon_bb INT NOT NULL,
  timestamp_unix BIGINT NOT NULL,
  count INT,
  PRIMARY KEY (id)
) ENGINE=INNODB;

CREATE TABLE IF NOT EXISTS cryme_classifiers (
  id INT AUTO_INCREMENT,
  log_loss FLOAT(53) NOT NULL,
  n_samples_train INT NOT NULL,
  n_samples_test INT NOT NULL,
  model_generated_on DATETIME NOT NULL,
  saved_to VARCHAR(255),
  PRIMARY KEY (id)
) ENGINE=INNODB;

DELIMITER //
CREATE PROCEDURE AddNewModel(log_loss_val FLOAT(53), n_samples_train_val INT, n_samples_test_val INT, saved_to_val VARCHAR(255))
  BEGIN
  INSERT INTO cryme_classifiers
    (log_loss, n_samples_train, n_samples_test, model_generated_on, saved_to)
    VALUES (log_loss_val, n_samples_train_val, n_samples_test_val, CURRENT_TIMESTAMP(), saved_to_val);
 END //
DELIMITER ;