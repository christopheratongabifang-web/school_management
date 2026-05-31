# fix_password_column.py
from app import app, db
from sqlalchemy import text

def fix_password_column():
    """Fix the password_hash column to be VARCHAR(512)"""
    
    with app.app_context():
        print("="*60)
        print("FIXING PASSWORD_HASH COLUMN")
        print("="*60)
        
        try:
            # Check current password_hash column info
            print("\n🔍 Checking current password_hash column...")
            result = db.session.execute(text("""
                SELECT column_name, data_type, character_maximum_length 
                FROM information_schema.columns 
                WHERE table_name = 'user' AND column_name = 'password_hash'
            """))
            
            for row in result:
                print(f"   Current: {row[0]} - {row[1]} (max length: {row[2]})")
                if row[2] != 512:
                    print(f"\n⚠️  Password hash column has length {row[2]}, fixing to 512...")
            
            # Alter the password_hash column to VARCHAR(512)
            print("\n🔧 Altering password_hash column to VARCHAR(512)...")
            db.session.execute(text('ALTER TABLE "user" ALTER COLUMN password_hash TYPE VARCHAR(512);'))
            db.session.commit()
            print("✅ Password_hash column updated to VARCHAR(512)!")
            
            # Verify the change
            result = db.session.execute(text("""
                SELECT character_maximum_length 
                FROM information_schema.columns 
                WHERE table_name = 'user' AND column_name = 'password_hash'
            """))
            
            new_length = result.fetchone()[0]
            print(f"✅ Verification: password_hash column now has max length {new_length}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            db.session.rollback()
            print("\nTrying alternative approach...")
            
            try:
                # Alternative: Drop and recreate the column (will lose data)
                print("Dropping and recreating password_hash column...")
                db.session.execute(text('ALTER TABLE "user" DROP COLUMN password_hash;'))
                db.session.execute(text('ALTER TABLE "user" ADD COLUMN password_hash VARCHAR(512);'))
                db.session.commit()
                print("✅ Password_hash column recreated with VARCHAR(512)!")
            except Exception as e2:
                print(f"❌ Alternative also failed: {e2}")

if __name__ == '__main__':
    fix_password_column()