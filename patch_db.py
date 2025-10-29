import sqlite3
import os

# Path to the database file
db_path = os.path.join(os.path.dirname(__file__), 'instance', 'sammy.db')

def patch_database():
    """
    Manually adds the project_id column to the equipment table if it doesn't exist.
    """
    if not os.path.exists(db_path):
        print(f"Error: Database file not found at '{db_path}'")
        return

    print(f"Connecting to database at '{db_path}'...")
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        print("Connection successful.")

        # Get the list of columns in the 'equipment' table
        cursor.execute("PRAGMA table_info(equipment)")
        columns = [info[1] for info in cursor.fetchall()]

        # Check if 'project_id' column already exists
        if 'project_id' in columns:
            print("Column 'project_id' already exists in 'equipment' table. No changes needed.")
        else:
            print("Column 'project_id' not found. Adding it now...")
            # Add the column. It will be nullable to avoid issues with existing rows.
            cursor.execute("ALTER TABLE equipment ADD COLUMN project_id INTEGER REFERENCES projects(id)")
            print("Successfully added 'project_id' column to 'equipment' table.")

        conn.commit()
        print("Database changes committed.")

    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
    finally:
        if conn:
            conn.close()
            print("Database connection closed.")

if __name__ == "__main__":
    patch_database()
