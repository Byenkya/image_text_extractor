from text_extractor import app, login_manager, db
from text_extractor.config import Config
from text_extractor.routes import (
    ImageViewerView, 
    GalleryView, 
    LoginView,
    UserCreationView,
    LogoutView,
    CaptureImageView
)
from flask_wtf.csrf import CSRFProtect
from text_extractor.models import User

# with open('secret.key', 'r') as f:
#     app.secret_key = f.read().strip()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


csrf = CSRFProtect(app)


#Register routes
app.add_url_rule('/login', view_func=LoginView.as_view('login'))
app.add_url_rule('/index', view_func=ImageViewerView.as_view('index'))  
app.add_url_rule('/gallery', view_func=GalleryView.as_view('gallery'))
app.add_url_rule('/create_user', view_func=UserCreationView.as_view('create_user'))
app.add_url_rule('/logout', view_func=LogoutView.as_view('logout'))
app.add_url_rule('/capture_image', view_func=CaptureImageView.as_view('capture_image'))

if __name__ == '__main__':
    with app.app_context():
        app.config.from_object(Config)
        db.create_all()
    app.run(host="192.168.43.157", debug=True)