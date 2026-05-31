# fix_db.py
import sys
import os
from app import app, db
from sqlalchemy import text

def fix_database():
    """Fix database issues without full reset"""
    
    with app.app_context():
        print("="*60)
        print("DATABASE FIX UTILITY")
        print("="*60)
        
        try:
            # Try to fix username column
            print("\n🔧 Fixing username column...")
            db.session.execute(text('ALTER TABLE "user" ALTER COLUMN username TYPE VARCHAR(64);'))
            db.session.commit()
            print("✅ Username column fixed!")
            
            # Try to update any existing admin
            print("\n🔧 Updating admin user...")
            from models import User
            
            admin_email = os.environ.get('INITIAL_ADMIN_EMAIL')
            admin = None
            if admin_email:
                admin = User.query.filter_by(email=admin_email).first()
            if admin:
                if len(admin.username) > 64:
                    admin.username = 'ADMIN'
                    db.session.commit()
                    print("✅ Admin username updated!")
                else:
                    print("✅ Admin username already OK!")
            else:
                print("ℹ️  No admin user found - ensure INITIAL_ADMIN_EMAIL is set for admin creation")
            
            print("\n" + "="*60)
            print("✅ DATABASE FIX COMPLETE!")
            print("="*60)
            print("\nNow run: python app.py\n")
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            print("\nTry running: python reset_and_fix.py")
            db.session.rollback()

if __name__ == '__main__':
    fix_database()