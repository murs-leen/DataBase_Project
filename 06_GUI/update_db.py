import mysql.connector

DB_CONFIG = {
    "host":     "localhost",
    "user":     "root",
    "password": "password",
    "database": "hms_db",
    "charset":  "utf8mb4"
}

def update():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # Add email column if not exists
        try:
            cur.execute("ALTER TABLE USERS ADD COLUMN email VARCHAR(100) UNIQUE;")
            print("Added email column.")
        except mysql.connector.Error as err:
            if err.errno == 1060: # Duplicate column name
                print("email column already exists.")
            else:
                print(f"Error adding email: {err}")
                
        # Remove Viewer role by modifying enum
        try:
            cur.execute("DELETE FROM USERS WHERE role='Viewer';")
            cur.execute("ALTER TABLE USERS MODIFY COLUMN role ENUM('Admin','Doctor','Staff') NOT NULL;")
            print("Modified role enum and deleted Viewer records.")
        except mysql.connector.Error as err:
            print(f"Error modifying role: {err}")
            
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Connection failed: {e}")

if __name__ == "__main__":
    update()
