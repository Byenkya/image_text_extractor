import os
from flask import current_app

def delete_image_file(filename):
    try:
        image_path = os.path.join(
            current_app.config['UPLOAD_FOLDER'],
            filename
        )
        os.remove(image_path)

    except Exception as e:
        raise e