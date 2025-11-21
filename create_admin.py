import os
from app import app, db, bcrypt
from app.models import User

def create_admin():
    with app.app_context():
        db.create_all() # Ensure tables exist with new schema
        
        admin_email = os.environ.get('ADMIN_EMAIL', 'admin@timepay.com')
        admin_password = os.environ.get('ADMIN_PASSWORD', 'admin123')
        
        # Check if admin exists
        admin = User.query.filter_by(email=admin_email).first()
        if not admin:
            hashed_password = bcrypt.generate_password_hash(admin_password).decode('utf-8')
            admin = User(
                username='Admin',
                email=admin_email,
                password=hashed_password,
                employee_id='ADMIN001',
                designation='System Administrator',
                department='IT',
                monthly_salary=50000,
                ot_rate=200,
                is_admin=True,
                role='super_admin'
            )
            db.session.add(admin)
            db.session.commit()
            print("Super Admin user created successfully.")
            print(f"Email: {admin_email}")
            print(f"Password: {admin_password}")
        else:
            print("Admin user already exists.")

if __name__ == '__main__':
    create_admin()
