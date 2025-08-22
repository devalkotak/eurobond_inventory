import csv
import sqlite3
from werkzeug.security import generate_password_hash
import os

# --- Configuration ---
# The name of the CSV file containing "username,password,role,status" data.
INPUT_FILE = 'users.csv'
# The name of the SQLite database file for users.
DB_FILE = 'users.db'

def import_users_from_csv():
    """
    Reads a CSV file with user data, connects to the SQLite database,
    and directly inserts the new users with hashed passwords.
    """
    
    if not os.path.exists(DB_FILE):
        print(f"Error: Database file '{DB_FILE}' not found. Please run the main app first to create it.")
        return

    try:
        # Connect to the SQLite database
        db = sqlite3.connect(DB_FILE)
        cursor = db.cursor()
        print(f"Successfully connected to {DB_FILE}.")
        
        with open(INPUT_FILE, 'r', newline='') as f:
            reader = csv.reader(f)
            
            # --- FIX: Skip the header row ---
            next(reader, None)
            
            for i, row in enumerate(reader, 2): # Start line count from 2 for user-friendly error messages
                # Skip empty rows
                if not row:
                    continue
                
                # Check for correct number of columns
                if len(row) != 4:
                    print(f"-- SKIPPING invalid line #{i} (format should be username,password,role,status): {','.join(row)}")
                    continue

                # Strip whitespace from all fields
                username, password, role, status = [field.strip() for field in row]
                
                # Validate role
                valid_roles = ['director', 'admin', 'viewer']
                if role.lower() not in valid_roles:
                    print(f"-- SKIPPING invalid role on line #{i} for user '{username}'. Role must be one of {valid_roles}.")
                    continue

                # Validate status
                valid_statuses = ['active', 'suspended']
                if status.lower() not in valid_statuses:
                    print(f"-- SKIPPING invalid status on line #{i} for user '{username}'. Status must be 'active' or 'suspended'.")
                    continue

                # Generate the secure hash for the password
                hashed_password = generate_password_hash(password)
                
                # Insert the user into the database
                try:
                    cursor.execute(
                        "INSERT INTO users (username, password, role, status) VALUES (?, ?, ?, ?)",
                        (username, hashed_password, role.lower(), status.lower())
                    )
                    print(f"Successfully added user: {username}")
                except sqlite3.IntegrityError:
                    # This error occurs if the username is not unique
                    print(f"-- SKIPPING user '{username}' because they already exist in the database.")

        # Commit the changes to the database and close the connection
        db.commit()
        print("\nDatabase update complete.")

    except FileNotFoundError:
        print(f"Error: The input file '{INPUT_FILE}' was not found.")
        print("Please create it with your 'username,password,role,status' list.")
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        if 'db' in locals() and db:
            db.close()

if __name__ == '__main__':
    import_users_from_csv()
