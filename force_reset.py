# force_reset.py
import sys
import os
from app import app, db
from sqlalchemy import text

def reset_database():
    """Complete database reset with proper error handling"""
    
    print("="*60)
    print("DATABASE RESET UTILITY")
    print("="*60)
    print("\n⚠️  WARNING: This will delete ALL data in the database!")
    confirm = input("Type 'YES' to confirm: ")
    
    if confirm != 'YES':
        print("Operation cancelled.")
        return
    
    with app.app_context():
        try:
            # Drop all tables
            print("\n📊 Dropping all tables...")
            db.drop_all()
            print("✅ All tables dropped!")
            
            # Create all tables fresh
            print("\n📊 Creating fresh tables...")
            db.create_all()
            print("✅ Tables created successfully!")
            
            # Verify user table schema
            print("\n🔍 Verifying user table schema...")
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            columns = inspector.get_columns('user')
            print("User table columns:")
            for col in columns:
                print(f"  - {col['name']}: {col['type']}")
            
            # Commit any pending changes
            db.session.commit()
            
            print("\n" + "="*60)
            print("✅ DATABASE RESET COMPLETE!")
            print("="*60)
            print("\nNow run: python app.py")
            print("This will recreate the admin user and all default data if INITIAL_ADMIN_EMAIL and INITIAL_ADMIN_PASSWORD are set in the environment.\n")
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            db.session.rollback()
            print("\nTry running: python fix_db.py")

if __name__ == '__main__':
    reset_database()