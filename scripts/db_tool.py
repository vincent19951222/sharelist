import os
import sys
import re
import subprocess
import time
from pathlib import Path

# Configuration
BACKEND_ENV_PATH = Path(__file__).parent.parent / "backend" / ".env"
BACKUP_DIR = Path(__file__).parent.parent / "backups"

def load_env_vars(env_path):
    """Simple parser for .env files to avoid external dependencies if possible"""
    config = {}
    if not env_path.exists():
        print(f"Error: .env file not found at {env_path}")
        sys.exit(1)
        
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, value = line.split("=", 1)
                config[key.strip()] = value.strip()
    return config

def parse_db_url(url):
    """
    Parses database URL.
    Handles: postgresql+asyncpg://user:pass@host:port/dbname
    Returns: (user, password, host, port, dbname)
    """
    if not url.startswith("postgresql"):
        print("Error: scripts/db_tool.py only supports PostgreSQL-compatible DATABASE_URL values.")
        print("Current DATABASE_URL does not look like PostgreSQL/Supabase. For local SQLite, skip backup/restore via this script.")
        sys.exit(1)

    # Remove driver info (e.g., +asyncpg) for standard tools
    clean_url = re.sub(r'\+[\w]+://', '://', url)
    
    # Regex to capture parts
    pattern = r"postgresql://([^:]+):([^@]+)@([^:/]+):(\d+)/(.+)"
    match = re.match(pattern, clean_url)
    
    if not match:
        print("Error: Could not parse DATABASE_URL. Format expected: postgresql://user:pass@host:port/dbname")
        sys.exit(1)
        
    return match.groups()

def run_docker_command(env_vars, command_args, operation_name):
    """Runs a postgres client command inside a Docker container"""
    
    user, password, host, port, dbname = parse_db_url(env_vars["DATABASE_URL"])
    
    # Use official Postgres image (alpine is small)
    image = "postgres:15-alpine"
    
    print(f"[{operation_name}] Connecting to {host} as {user}...")
    
    docker_cmd = [
        "docker", "run", "--rm", "-i",
        "-e", f"PGPASSWORD={password}",
        "-v", f"{BACKUP_DIR.absolute()}:/backups",
        image
    ]
    
    full_cmd = docker_cmd + command_args
    
    try:
        # Check if docker is available
        subprocess.run(["docker", "--version"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Error: Docker is not installed or not running. Please start Docker Desktop.")
        sys.exit(1)

    return subprocess.run(full_cmd, env=os.environ.copy())

def backup():
    env_vars = load_env_vars(BACKEND_ENV_PATH)
    user, _, host, port, dbname = parse_db_url(env_vars["DATABASE_URL"])
    
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = f"backup_{timestamp}.sql"
    
    # Ensure backup dir exists
    BACKUP_DIR.mkdir(exist_ok=True)
    
    print(f"Starting Backup to backups/{filename}...")
    
    # pg_dump command
    # -Fc (Custom format) is better for restores, but Plain SQL is readable. 
    # Let's use Plain SQL for this educational context so user can read it.
    cmd_args = [
        "pg_dump",
        "-h", host,
        "-p", port,
        "-U", user,
        "-d", dbname,
        "--clean",     # Include DROP commands
        "--if-exists", # Avoid error if DB empty
        "-f", f"/backups/{filename}"
    ]
    
    result = run_docker_command(env_vars, cmd_args, "Backup")
    
    if result.returncode == 0:
        print(f"✅ Backup successful! File: {BACKUP_DIR / filename}")
    else:
        print("❌ Backup failed.")

def restore(file_path):
    if not file_path:
        print("Error: Please specify the backup file to restore.")
        print("Usage: python scripts/db_tool.py restore <filename>")
        sys.exit(1)
        
    target_file = BACKUP_DIR / file_path
    if not target_file.exists():
         # Try finding it relative to current dir just in case
         target_file = Path(file_path)
         if not target_file.exists():
            print(f"Error: Backup file not found at {target_file}")
            sys.exit(1)
    
    print(f"⚠️  WARNING: This will OVERWRITE the database.")
    print(f"Target File: {target_file.name}")
    confirm = input("Type 'CONFIRM' to proceed: ")
    
    if confirm != "CONFIRM":
        print("Operation cancelled.")
        return

    env_vars = load_env_vars(BACKEND_ENV_PATH)
    user, _, host, port, dbname = parse_db_url(env_vars["DATABASE_URL"])
    
    print(f"Starting Restore from {target_file.name}...")
    
    # psql command
    cmd_args = [
        "psql",
        "-h", host,
        "-p", port,
        "-U", user,
        "-d", dbname,
        "-f", f"/backups/{target_file.name}"
    ]
    
    result = run_docker_command(env_vars, cmd_args, "Restore")
    
    if result.returncode == 0:
        print(f"✅ Restore successful!")
    else:
        print("❌ Restore failed.")

def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/db_tool.py [backup|restore] [filename]")
        sys.exit(1)
        
    action = sys.argv[1]
    
    if action == "backup":
        backup()
    elif action == "restore":
        filename = sys.argv[2] if len(sys.argv) > 2 else None
        restore(filename)
    else:
        print(f"Unknown command: {action}")

if __name__ == "__main__":
    main()
