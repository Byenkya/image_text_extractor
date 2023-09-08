with open('text_extractor/secret.key', 'r') as f:
    secret_key = f.read().strip()

class Config:
    UPLOAD_FOLDER = 'text_extractor/static/uploads'
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    SECRET_KEY = secret_key