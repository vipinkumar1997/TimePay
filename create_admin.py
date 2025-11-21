from app import app, db, bcrypt
from app.models import User

def create_admin():
    with app.app_context():
        db.create_all() # Ensure tables exist with new schema
        
        # Check if admin exists
        admin = User.query.filter_by(email='admin@timepay.com').first()
        if not admin:
            hashed_password = bcrypt.generate_password_hash('admin123').decode('utf-8')
            admin = User(
                username='Admin',
                email='admin@timepay.com',
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
            print("Email: admin@timepay.com")
            print("Password: admin123")
        else:
            print("Admin user already exists.")

if __name__ == '__main__':
    create_admin()
