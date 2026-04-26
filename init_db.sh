#!/bin/bash
echo "Installing DDL Schema..."
sudo mysql -u root < 02_DDL_Schema.sql
echo "Creating MySQL app user..."
sudo mysql -u root -e "CREATE USER IF NOT EXISTS 'hms_user'@'localhost' IDENTIFIED BY 'password'; GRANT ALL PRIVILEGES ON hms_db.* TO 'hms_user'@'localhost'; FLUSH PRIVILEGES;"
echo "Inserting initial data..."
sudo mysql -u root hms_db < 03_Insert_Data.sql
echo "Programming stored views, procedures..."
sudo mysql -u root hms_db < 05_Stored_Programming.sql
echo "Done!"
