#!/usr/bin/env python
"""
Merge team groups from two SQLite databases, preserving unique entries from both sources.
Usage: python merge_team_groups.py <target_db_path> <source_db_path>

Example: python merge_team_groups.py /app/data/team_groups.db /app/backup_data/team_groups.db
"""

import os
import sys
import sqlite3

def get_team_groups(db_path):
    """Get all team groups and their members from a database."""
    if not os.path.exists(db_path):
        print(f"Database does not exist: {db_path}")
        return {}

    conn = sqlite3.connect(db_path)
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

        return team_groups
    except sqlite3.Error as e:
        print(f"Error retrieving team groups from {db_path}: {str(e)}")
        return {}
    finally:
        conn.close()

def merge_team_groups(target_db, source_db):
    """Merge team groups from source database into target database."""
    target_groups = get_team_groups(target_db)
    source_groups = get_team_groups(source_db)

    # If target is empty but source has data, just copy the source file
    if not target_groups and source_groups:
        print(f"Target database is empty, copying source database")
        import shutil
        shutil.copy2(source_db, target_db)
        print(f"Copied {source_db} to {target_db}")
        return True

    # If source is empty, keep target as is
    if not source_groups:
        print(f"Source database is empty, keeping target database unchanged")
        return True

    # Check for fake team groups
    fake_groups = {"Premier League", "NC Teams"}
    has_only_fake_groups = all(group in fake_groups for group in target_groups.keys())

    if has_only_fake_groups and source_groups:
        print(f"Target database has only fake groups, copying source database")
        import shutil
        shutil.copy2(source_db, target_db)
        print(f"Copied {source_db} to {target_db}")
        return True

    # Both databases have valid data, perform a merge
    conn = sqlite3.connect(target_db)
    cursor = conn.cursor()

    try:
        # Begin transaction
        conn.execute("BEGIN TRANSACTION")

        # Merge team groups from source to target
        for group_name, teams in source_groups.items():
            if group_name in target_groups:
                # Group exists in target, merge team members
                print(f"Merging team members for group: {group_name}")

                # Get the group ID
                cursor.execute("SELECT id FROM team_groups WHERE name = ?", (group_name,))
                group_id = cursor.fetchone()[0]

                # Add missing team members
                for team in teams:
                    if team not in target_groups[group_name]:
                        print(f"  Adding team '{team}' to group '{group_name}'")
                        cursor.execute(
                            "INSERT OR IGNORE INTO team_group_members (group_id, team_name) VALUES (?, ?)",
                            (group_id, team)
                        )
            else:
                # Group doesn't exist in target, add it
                print(f"Adding new group: {group_name}")
                cursor.execute(
                    "INSERT INTO team_groups (name) VALUES (?)",
                    (group_name,)
                )
                group_id = cursor.lastrowid

                # Add all team members
                for team in teams:
                    cursor.execute(
                        "INSERT INTO team_group_members (group_id, team_name) VALUES (?, ?)",
                        (group_id, team)
                    )

        # Commit the changes
        conn.commit()
        print(f"Successfully merged team groups from {source_db} to {target_db}")
        return True
    except sqlite3.Error as e:
        conn.rollback()
        print(f"Error merging team groups: {str(e)}")
        return False
    finally:
        conn.close()

def main():
    if len(sys.argv) != 3:
        print("Usage: python merge_team_groups.py <target_db_path> <source_db_path>")
        sys.exit(1)

    target_db = sys.argv[1]
    source_db = sys.argv[2]

    print(f"Merging team groups from {source_db} to {target_db}")

    if not os.path.exists(source_db):
        print(f"Source database does not exist: {source_db}")
        sys.exit(1)

    success = merge_team_groups(target_db, source_db)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()