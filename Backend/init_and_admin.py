import sys
sys.path.append('D:/Claim_Sight_AI/Backend')
from app import create_app, db
from app.models.user import User

app = create_app()
with app.app_context():
    db.create_all()
    user = User.query.get(1)
    if user:
        user.role = 'admin'
        db.session.commit()
        print('User 1 set to admin')
    else:
        print('User 1 not found')

