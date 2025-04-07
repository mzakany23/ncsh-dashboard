import os
import sqlite3
import duckdb

def init_duckdb_connection(parquet_file):
    """Initialize DuckDB connection and load soccer data."""
    try:
        if not os.path.exists(parquet_file):
            raise FileNotFoundError(f"Parquet file not found at: {parquet_file}")

        conn = duckdb.connect(database=':memory:')
        conn.execute(f"CREATE OR REPLACE TABLE soccer_data AS SELECT * FROM '{parquet_file}'")
        print(f"Successfully initialized DuckDB connection and loaded data from {parquet_file}")
        return conn
    except Exception as e:
        print(f"Error initializing DuckDB connection: {str(e)}")
        raise

def get_teams(conn):
    """Get list of teams from the soccer data."""
    try:
        teams_query = """
        SELECT DISTINCT home_team AS team FROM soccer_data
        UNION
        SELECT DISTINCT away_team AS team FROM soccer_data
        ORDER BY team
        """
        teams_df = conn.execute(teams_query).fetchdf()
        teams = teams_df['team'].tolist()
        print(f"Successfully retrieved {len(teams)} teams")
        return teams
    except Exception as e:
        print(f"Error retrieving teams: {str(e)}")
        raise

def get_date_range(conn):
    """Get min and max dates from the soccer data."""
    try:
        date_range_query = """
        SELECT MIN(date) AS min_date, MAX(date) AS max_date FROM soccer_data
        """
        date_range_df = conn.execute(date_range_query).fetchdf()
        min_date = date_range_df['min_date'][0].strftime('%Y-%m-%d')
        max_date = date_range_df['max_date'][0].strftime('%Y-%m-%d')
        print(f"Date range: {min_date} to {max_date}")
        return min_date, max_date
    except Exception as e:
        print(f"Error retrieving date range: {str(e)}")
        raise

def init_db():
    init_team_db()


def init_team_db():
    """Initialize the SQLite database for team groups."""
    # Always use the absolute path that matches the LiteFS mount point in deployment
    # But fall back to the relative path for local development
    if os.path.exists('/app/data'):
        # In production (Docker/Fly.io)
        db_path = "/app/data/team_groups.db"
    else:
        # Local development
        dir_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
        os.makedirs(dir_path, exist_ok=True)
        db_path = os.path.join(dir_path, 'team_groups.db')

    print(f"Initializing SQLite database at {db_path}")

    # Check directory and log database info
    dir_path = os.path.dirname(db_path)
    if not os.path.exists(dir_path):
        print(f"Creating directory: {dir_path}")
        os.makedirs(dir_path, exist_ok=True)

    # Log existing database info before connecting
    if os.path.exists(db_path):
        print(f"Database already exists, size: {os.path.getsize(db_path)} bytes")
    else:
        print(f"Database file does not exist, will be created")

    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Enable foreign key support
    cursor.execute("PRAGMA foreign_keys = ON")

    # Set journal mode to WAL for better concurrency
    cursor.execute("PRAGMA journal_mode = WAL")

    # Create the team_groups table if it doesn't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS team_groups (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Create the team_group_members table if it doesn't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS team_group_members (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        group_id INTEGER NOT NULL,
        team_name TEXT NOT NULL,
        FOREIGN KEY (group_id) REFERENCES team_groups(id) ON DELETE CASCADE,
        UNIQUE(group_id, team_name)
    )
    ''')

    # Commit the changes
    conn.commit()

    # Check if we need to create default team groups
    cursor.execute("SELECT COUNT(*) FROM team_groups")
    group_count = cursor.fetchone()[0]

    if group_count == 0:
        print("No team groups found in database, creating default groups")
        create_default_team_groups(conn)
    else:
        print(f"Found {group_count} existing team groups, skipping default creation")

    # Close the connection
    conn.close()


def create_default_team_groups(conn):
    """Create default team groups if none exist."""
    try:
        # Define default team groups
        default_groups = {
            "Top Teams": ["Real Madrid", "Barcelona", "Bayern Munich", "Manchester City", "Liverpool"],
            "NC Teams": ["Charlotte FC", "North Carolina FC", "NC Courage"],
            "Premier League": ["Manchester City", "Liverpool", "Chelsea", "Arsenal", "Tottenham", "Manchester United"]
        }

        cursor = conn.cursor()

        # Begin transaction
        conn.execute("BEGIN TRANSACTION")

        for group_name, teams in default_groups.items():
            print(f"Creating default team group: {group_name} with {len(teams)} teams")

            # Create the team group
            cursor.execute("INSERT INTO team_groups (name) VALUES (?)", (group_name,))
            group_id = cursor.lastrowid

            # Add team members
            for team in teams:
                cursor.execute(
                    "INSERT INTO team_group_members (group_id, team_name) VALUES (?, ?)",
                    (group_id, team)
                )

        # Commit the changes
        conn.commit()
        print("Successfully created default team groups")

    except sqlite3.Error as e:
        conn.rollback()
        print(f"Error creating default team groups: {str(e)}")


def get_db_connection():
    """Get a SQLite database connection."""
    # Always use the absolute path that matches the LiteFS mount point in deployment
    # But fall back to the relative path for local development
    if os.path.exists('/app/data'):
        # In production (Docker/Fly.io)
        db_path = "/app/data/team_groups.db"
    else:
        # Local development
        dir_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
        os.makedirs(dir_path, exist_ok=True)
        db_path = os.path.join(dir_path, 'team_groups.db')

    print(f"Connecting to database at {db_path}")

    # Add more detailed debugging
    if os.path.exists(db_path):
        print(f"Database file exists, size: {os.path.getsize(db_path)} bytes")
        # Print file permissions
        print(f"File permissions: {oct(os.stat(db_path).st_mode)[-3:]}")
    else:
        print(f"WARNING: Database file does not exist at {db_path}")

    # Connect to the database and enable foreign keys
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")

    # Add journaling mode logging
    pragma_journal = conn.execute("PRAGMA journal_mode").fetchone()[0]
    print(f"SQLite journal mode: {pragma_journal}")

    return conn


def create_team_group(name, teams):
    """Create a new team group with the specified teams."""
    if not name or not teams:
        print(f"Error: Cannot create team group with empty name or no teams")
        return False

    # Check if a group with this name already exists
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Add transaction begin
        conn.execute("BEGIN IMMEDIATE TRANSACTION")

        # Check if the group already exists
        cursor.execute("SELECT id, name FROM team_groups WHERE name = ?", (name,))
        existing = cursor.fetchone()

        if existing:
            group_id = existing[0]
            print(f"Group '{name}' already exists with ID {group_id}")

            # Option: Return success but only if the group exists with the same teams
            cursor.execute("SELECT team_name FROM team_group_members WHERE group_id = ? ORDER BY team_name", (group_id,))
            existing_teams = [row[0] for row in cursor.fetchall()]

            # Check if the teams are the same
            if set(existing_teams) == set(teams):
                print(f"Group '{name}' already exists with the same teams")
                return True

            print(f"Cannot create duplicate group with different teams. The group already has these teams: {existing_teams}")
            return False

        # Create the team group
        cursor.execute("INSERT INTO team_groups (name) VALUES (?)", (name,))
        group_id = cursor.lastrowid

        # Add team members
        for team in teams:
            cursor.execute(
                "INSERT INTO team_group_members (group_id, team_name) VALUES (?, ?)",
                (group_id, team)
            )

        conn.commit()

        # Verify the data was written by reading it back
        cursor.execute("SELECT id FROM team_groups WHERE name = ?", (name,))
        group_id_check = cursor.fetchone()
        if group_id_check:
            db_path = conn.execute('PRAGMA database_list').fetchone()[2]
            print(f"Successfully created team group '{name}' with {len(teams)} teams at {db_path}")
            print(f"Verified team group '{name}' (ID: {group_id_check[0]}) was successfully saved to {db_path}")
            if os.path.exists(db_path):
                print(f"Database file size after commit: {os.path.getsize(db_path)} bytes")
        else:
            print(f"WARNING: Failed to verify team group '{name}' was saved!")

        return True
    except sqlite3.Error as e:
        conn.rollback()
        print(f"Database error creating team group: {str(e)}")
        return False
    finally:
        conn.close()


def get_team_groups():
    """Get all team groups from the database."""
    print(f"Retrieving team groups from {get_db_connection().execute('PRAGMA database_list').fetchone()[2]}")

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Get all team groups
        cursor.execute("SELECT id, name FROM team_groups ORDER BY name")
        groups = cursor.fetchall()

        # Create a dictionary of team groups
        team_groups = {}
        for group_id, group_name in groups:
            # Get all teams in the group
            cursor.execute("SELECT team_name FROM team_group_members WHERE group_id = ?", (group_id,))
            teams = [row[0] for row in cursor.fetchall()]
            team_groups[group_name] = teams

        print(f"Found {len(team_groups)} team groups in database")
        return team_groups
    except sqlite3.Error as e:
        print(f"Error retrieving team groups: {str(e)}")
        return {}
    finally:
        conn.close()


def update_team_group(name, teams, new_name=None):
    """Update an existing team group."""
    if not name:
        return False

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Get the group ID
        cursor.execute("SELECT id FROM team_groups WHERE name = ?", (name,))
        row = cursor.fetchone()

        if not row:
            print(f"Team group '{name}' not found")
            return False

        group_id = row[0]

        # Start a transaction
        conn.execute("BEGIN TRANSACTION")

        # Update the name if a new name is provided and it's different
        if new_name and new_name != name:
            # Check if the new name already exists
            cursor.execute("SELECT id FROM team_groups WHERE name = ? AND id != ?", (new_name, group_id))
            if cursor.fetchone():
                print(f"Cannot rename group to '{new_name}' as a group with that name already exists")
                conn.rollback()
                return False

            cursor.execute("UPDATE team_groups SET name = ? WHERE id = ?", (new_name, group_id))
            print(f"Renamed team group from '{name}' to '{new_name}'")
            name = new_name  # Use the new name for the rest of the function

        # Delete existing members
        cursor.execute("DELETE FROM team_group_members WHERE group_id = ?", (group_id,))

        # Insert new members
        for team in teams:
            cursor.execute(
                "INSERT INTO team_group_members (group_id, team_name) VALUES (?, ?)",
                (group_id, team)
            )

        conn.commit()
        print(f"Updated team group '{name}' with {len(teams)} teams")
        return True
    except sqlite3.Error as e:
        print(f"Error updating team group: {str(e)}")
        conn.rollback()
        return False
    finally:
        conn.close()


def delete_team_group(name):
    """Delete a team group."""
    if not name:
        print(f"Error: Cannot delete team group with empty name")
        return False

    print(f"Attempting to delete team group: '{name}'")

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Start a transaction
        conn.execute("BEGIN TRANSACTION")

        # Enable foreign keys for cascading deletes
        cursor.execute("PRAGMA foreign_keys = ON")

        # First check if the group exists
        cursor.execute("SELECT id FROM team_groups WHERE name = ?", (name,))
        group = cursor.fetchone()

        if not group:
            print(f"Error: Team group '{name}' not found in database")
            return False

        group_id = group[0]
        print(f"Found team group with ID: {group_id}")

        # Count members to be deleted
        cursor.execute("SELECT COUNT(*) FROM team_group_members WHERE group_id = ?", (group_id,))
        member_count = cursor.fetchone()[0]
        print(f"Team group has {member_count} members that will be deleted")

        # First delete the members explicitly, ignoring errors
        try:
            cursor.execute("DELETE FROM team_group_members WHERE group_id = ?", (group_id,))
            print(f"Deleted {member_count} team members")
        except sqlite3.Error as e:
            print(f"Warning when deleting members: {str(e)}")
            # Continue with deletion of the group

        # Then delete the team group
        cursor.execute("DELETE FROM team_groups WHERE id = ?", (group_id,))

        # Verify the deletion
        cursor.execute("SELECT id FROM team_groups WHERE id = ?", (group_id,))
        if cursor.fetchone():
            print(f"Error: Group {group_id} still exists after attempted deletion")
            conn.rollback()
            return False

        # Commit and return success
        conn.commit()
        print(f"Successfully deleted team group '{name}' with ID {group_id}")
        return True
    except sqlite3.Error as e:
        print(f"Database error deleting team group: {str(e)}")
        conn.rollback()
        return False
    finally:
        conn.close()