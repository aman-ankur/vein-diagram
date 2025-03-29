#!/bin/bash

# Run the profile migration script
echo "Running profile migration script..."

# Navigate to the backend directory to ensure we're running in the right location
cd "$(dirname "$0")"
echo "Working directory: $(pwd)"

# Check if the database file exists
if [ -f "vein_diagram.db" ]; then
    echo "Using existing database: $(pwd)/vein_diagram.db"
    echo "Database size: $(du -h vein_diagram.db | cut -f1)"
else
    echo "Warning: Database file not found in $(pwd)"
fi

# Run the migration script
python3 db_schema_migration_profile.py

# Check if the migration was successful
if [ $? -eq 0 ]; then
    echo "Migration completed successfully!"
    echo "The database now has profile support."
    
    # Verify tables in the database
    echo ""
    echo "Verifying database tables:"
    echo "-------------------------"
    sqlite3 vein_diagram.db ".tables"
    echo "-------------------------"
    
    echo ""
    echo "Next steps:"
    echo "1. Start the backend server: python run.py"
    echo "2. Start the frontend: cd ../frontend && npm run dev"
    echo "3. Create and manage profiles at http://localhost:3000/profiles"
else
    echo "Migration failed. Please check the error messages above."
    exit 1
fi 