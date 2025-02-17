from sqlalchemy.orm import Session
from fastapi import UploadFile
import os
from datetime import datetime
from core import models

def save_content_to_folder_background(
    file: UploadFile, 
    username: str, 
    title: str, 
    caption: str,  
    content_dir: str = "content_database"  
):
    try:
        # Ensure the root content directory exists
        if not isinstance(content_dir, str):
            raise ValueError("content_dir should be a string path.")
        
        if not os.path.exists(content_dir):
            os.makedirs(content_dir)

        # Create a folder named after the user inside the content database directory (if it doesn't already exist)
        user_folder = os.path.join(content_dir, username)
        if not os.path.exists(user_folder):
            os.makedirs(user_folder)

        # Save the file with a timestamped name to avoid name clashes
        file_location = os.path.join(user_folder, f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}")
        
        # Write the uploaded file content to the file location
        with open(file_location, "wb") as buffer:
            buffer.write(file.file.read())

        # Return the necessary information (content to be saved in the main thread)
        return {
            "username": username,
            "title": title,
            "caption": caption,
            "file": file_location,
            "created_at": datetime.now()
        }

    except Exception as e:
        raise Exception(f"Error while saving content: {str(e)}")
