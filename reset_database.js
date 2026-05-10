/*
 * One-command DB reset runner for this project (MySQL).
 * Usage:
 *   node reset_database.js
 *
 * Optional env overrides:
 *   MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE
 */

const { execSync, spawnSync } = require("child_process");
const path = require("path");

const host = process.env.MYSQL_HOST || "localhost";
const port = process.env.MYSQL_PORT || "3306";
const user = process.env.MYSQL_USER || "root";
const password = process.env.MYSQL_PASSWORD || "password";
const database = process.env.MYSQL_DATABASE || "hms_db";
const sqlPath = path.join(__dirname, "reset_database.sql");

function quoteArg(v) {
  return `"${String(v).replace(/"/g, '\\"')}"`;
}

try {
  console.log("Running reset_database.sql against MySQL...");
  const cmd =
    `mysql -h ${quoteArg(host)} -P ${quoteArg(port)} -u ${quoteArg(user)} ` +
    `-p${quoteArg(password)} ${quoteArg(database)} < ${quoteArg(sqlPath)}`;

  execSync(cmd, { stdio: "inherit", shell: true });
  console.log("Database reset completed.");
} catch (err) {
  console.warn("mysql CLI not available or failed. Trying Python connector fallback...");

  const pyCode = `
import mysql.connector
conn = mysql.connector.connect(
    host=${JSON.stringify(host)},
    port=int(${JSON.stringify(port)}),
    user=${JSON.stringify(user)},
    password=${JSON.stringify(password)},
    database=${JSON.stringify(database)}
)
cur = conn.cursor()
tables = [
    "PRESCRIPTION_DETAILS","BILLING","ADMISSION","APPOINTMENT","PRESCRIPTION",
    "USERS","NURSE","DOCTOR","ROOM","PATIENT","STAFF","MEDICINE","DEPARTMENT"
]
cur.execute("SET FOREIGN_KEY_CHECKS = 0")
for t in tables:
    cur.execute(f"TRUNCATE TABLE {t}")
for t in tables:
    cur.execute(f"ALTER TABLE {t} AUTO_INCREMENT = 1")
cur.execute("SET FOREIGN_KEY_CHECKS = 1")
conn.commit()
for t in tables:
    cur.execute(f"SELECT COUNT(*) FROM {t}")
    print(f"{t}: {cur.fetchone()[0]}")
cur.close()
conn.close()
print("Database reset completed.")
`;

  const py = spawnSync("python", ["-c", pyCode], { stdio: "inherit" });
  if (py.status !== 0) {
    console.error("Database reset failed in fallback mode.");
    console.error("Check credentials in env vars or app config.");
    process.exit(1);
  }
}
