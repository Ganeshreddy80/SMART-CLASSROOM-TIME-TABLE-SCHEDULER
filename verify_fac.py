from app import app
from models import Faculty

with app.app_context():
    f = Faculty.query.first()
    pw_guess = f.name.split()[1].lower() + '#SRM2026'
    print(f"Name: {f.name}")
    print(f"Checking {pw_guess}:", f.check_password(pw_guess))
    
    pw_guess2 = "password123"
    print(f"Checking {pw_guess2}:", f.check_password(pw_guess2))

    # Also what about the default password generator?
    from models import generate_default_password
    pw_guess3 = generate_default_password(f.name)
    print(f"Checking {pw_guess3}:", f.check_password(pw_guess3))

    pw_guess4 = "faculty123"
    print(f"Checking {pw_guess4}:", f.check_password(pw_guess4))
