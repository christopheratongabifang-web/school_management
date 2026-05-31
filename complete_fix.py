# complete_fix.py
from app import app, db
import os
from sqlalchemy import text
import sys

def complete_fix():
    """Complete database fix - updates all column lengths"""
    
    with app.app_context():
        print("="*60)
        print("COMPLETE DATABASE FIX")
        print("="*60)
        
        # Fix username column
        print("\n1. Fixing username column...")
        try:
            db.session.execute(text('ALTER TABLE "user" ALTER COLUMN username TYPE VARCHAR(64);'))
            db.session.commit()
            print("   ✅ Username column fixed")
        except Exception as e:
            print(f"   ⚠️ Username column already correct or error: {e}")
        
        # Fix password_hash column
        print("\n2. Fixing password_hash column...")
        try:
            db.session.execute(text('ALTER TABLE "user" ALTER COLUMN password_hash TYPE VARCHAR(512);'))
            db.session.commit()
            print("   ✅ Password_hash column fixed to VARCHAR(512)")
        except Exception as e:
            print(f"   ⚠️ Could not fix password_hash: {e}")
        
        # Fix email column
        print("\n3. Fixing email column...")
        try:
            db.session.execute(text('ALTER TABLE "user" ALTER COLUMN email TYPE VARCHAR(255);'))
            db.session.commit()
            print("   ✅ Email column fixed")
        except Exception as e:
            print(f"   ⚠️ Could not fix email: {e}")
        
        # Verify changes
        print("\n4. Verifying changes...")
        result = db.session.execute(text("""
            SELECT column_name, data_type, character_maximum_length 
            FROM information_schema.columns 
            WHERE table_name = 'user' 
            ORDER BY column_name
        """))
        
        print("\n   Current user table schema:")
        for row in result:
            print(f"   - {row[0]}: {row[1]} (max: {row[2]})")
        
        # Now try to create admin user directly
        print("\n5. Creating admin user directly...")
        from models import User
        from werkzeug.security import generate_password_hash
        
        try:
            # Create new admin only if provided via environment variables
            env_email = os.environ.get('INITIAL_ADMIN_EMAIL')
            env_password = os.environ.get('INITIAL_ADMIN_PASSWORD')
            env_username = os.environ.get('INITIAL_ADMIN_USERNAME', 'ADMIN')

            if env_email and env_password:
                db.session.execute(text("DELETE FROM \"user\" WHERE email = :email OR role = 'SUPER_ADMIN';"), {'email': env_email})
                db.session.commit()

                admin = User(
                    username=env_username,
                    email=env_email,
                    role='SUPER_ADMIN'
                )
                admin.set_password(env_password)
                db.session.add(admin)
                db.session.commit()
                print("   ✅ Admin user created successfully from environment variables.")
                print("   Admin account created. Change the password immediately after first login.")
            else:
                print("   ⚠️ No INITIAL_ADMIN_EMAIL or INITIAL_ADMIN_PASSWORD env vars set; skipping admin creation.")
            
        except Exception as e:
            print(f"   ❌ Error creating admin: {e}")
            db.session.rollback()
            
            # Try with raw SQL as fallback
            print("\n   Trying raw SQL insertion...")
            try:
                env_email = os.environ.get('INITIAL_ADMIN_EMAIL')
                env_password = os.environ.get('INITIAL_ADMIN_PASSWORD')
                if env_email and env_password:
                    password_hash = generate_password_hash(env_password)
                    db.session.execute(text("""
                        INSERT INTO "user" (username, email, password_hash, role) 
                        VALUES (:username, :email, :pwd, 'SUPER_ADMIN')
                    """), {'username': os.environ.get('INITIAL_ADMIN_USERNAME', 'ADMIN'), 'email': env_email, 'pwd': password_hash})
                    db.session.commit()
                    print("   ✅ Admin created via raw SQL from environment variables!")
                else:
                    print("   ⚠️ No admin credentials set in environment; cannot create admin.")
            except Exception as e2:
                print(f"   ❌ Raw SQL also failed: {e2}")
        
        print("\n" + "="*60)
        print("✅ FIX COMPLETE!")
        print("="*60)
        print("\nNow run: python app.py\n")

if __name__ == '__main__':
    complete_fix()