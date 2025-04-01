#!/usr/bin/env python

import os
import sys
from sqlalchemy import create_engine, select, delete
from sqlalchemy.orm import sessionmaker, Session
from dotenv import load_dotenv

# Adjust the path to import modules from the backend app directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(SCRIPT_DIR)
APP_DIR = os.path.join(BACKEND_DIR, 'app')
sys.path.insert(0, BACKEND_DIR) # Add backend directory to path

# Now we can import from app
try:
    from app.models.profile_model import Profile
    from app.models.biomarker_model import Biomarker
    from app.models.pdf_model import PDF
    from app.db.database import Base # Needed if creating tables, but good practice
    # Assuming database URL is in .env file in the backend directory
    dotenv_path = os.path.join(BACKEND_DIR, '.env')
    load_dotenv(dotenv_path=dotenv_path)
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL environment variable not set. Ensure .env file exists in backend/ directory.")

except ImportError as e:
    print(f"Error importing application modules: {e}")
    print("Please ensure you are running this script from the 'backend/scripts/' directory or adjust the path accordingly.")
    sys.exit(1)
except ValueError as e:
    print(e)
    sys.exit(1)


def get_profiles(session: Session):
    """Fetches all profiles from the database."""
    return session.execute(select(Profile.id, Profile.name).order_by(Profile.name)).all()

def delete_associated_data(session: Session, profile_id: str):
    """Deletes biomarkers and PDFs associated with a profile."""
    biomarker_delete_stmt = delete(Biomarker).where(Biomarker.profile_id == profile_id)
    pdf_delete_stmt = delete(PDF).where(PDF.profile_id == profile_id)

    biomarker_result = session.execute(biomarker_delete_stmt)
    pdf_result = session.execute(pdf_delete_stmt)

    return biomarker_result.rowcount, pdf_result.rowcount

def delete_profile(session: Session, profile_id: str):
    """Deletes the profile itself."""
    profile_delete_stmt = delete(Profile).where(Profile.id == profile_id)
    result = session.execute(profile_delete_stmt)
    return result.rowcount

def main():
    """Main function to run the CLI tool."""
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    with SessionLocal() as session:
        try:
            profiles = get_profiles(session)

            if not profiles:
                print("No profiles found in the database.")
                return

            print("Available Profiles:")
            for i, (profile_id, profile_name) in enumerate(profiles):
                print(f"{i + 1}: {profile_name} (ID: {profile_id})")

            while True:
                try:
                    selection = input(f"Enter the number of the profile to delete data for (1-{len(profiles)}): ")
                    selected_index = int(selection) - 1
                    if 0 <= selected_index < len(profiles):
                        selected_profile_id, selected_profile_name = profiles[selected_index]
                        break
                    else:
                        print("Invalid selection. Please enter a number from the list.")
                except ValueError:
                    print("Invalid input. Please enter a number.")

            print(f"\nYou have selected profile: {selected_profile_name} (ID: {selected_profile_id})")

            confirm_data = input("WARNING: This will permanently delete all associated Biomarker and PDF data for this profile. Are you sure? (yes/no): ").lower().strip()

            if confirm_data.startswith('y'): # Accept 'y' or 'yes'
                biomarkers_deleted, pdfs_deleted = delete_associated_data(session, selected_profile_id)
                print(f"Deleted {biomarkers_deleted} biomarker entries.")
                print(f"Deleted {pdfs_deleted} PDF entries.")

                confirm_profile = input(f"Do you also want to delete the profile '{selected_profile_name}' itself? (yes/no): ").lower().strip()
                if confirm_profile.startswith('y'): # Accept 'y' or 'yes'
                    profile_deleted_count = delete_profile(session, selected_profile_id)
                    if profile_deleted_count > 0:
                        print(f"Deleted profile '{selected_profile_name}'.")
                    else:
                        print(f"Could not find or delete profile '{selected_profile_name}'.")
                else:
                    print("Profile entry was not deleted.")

                session.commit()
                print("Changes committed to the database.")

            else:
                print("Operation cancelled. No data was deleted.")

        except Exception as e:
            print(f"An error occurred: {e}")
            session.rollback()
            print("Transaction rolled back.")
        finally:
            print("Closing database session.")

if __name__ == "__main__":
    main()
