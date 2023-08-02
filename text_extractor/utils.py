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
    
def save_image_on_server(image_data, username):
    # Remove the "data:image/png;base64," prefix from the base64 data
    image_data = image_data.split(',')[1]

    # Save the image in a "static/uploads" folder with the username as the filename
    with open(f'static/uploads/{username}.png', 'wb') as f:
        f.write(base64.b64decode(image_data))