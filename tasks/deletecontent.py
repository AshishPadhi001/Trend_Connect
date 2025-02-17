import shutil
import os

def delete_content_folder_background(username: str):
    try:
        # Define the folder path inside the content_database directory
        folder_path = os.path.join("content_database", username)  # Ensure the folder is inside content_database
        
        # Check if the folder exists and delete
        if os.path.exists(folder_path):
            shutil.rmtree(folder_path)  # Deletes the entire folder and its contents
            print(f"Folder for user '{username}' deleted successfully.")
        else:
            print(f"Folder for user '{username}' does not exist.")
    except Exception as e:
        # Error handling if folder deletion fails
        print(f"Error occurred while deleting folder for user '{username}': {str(e)}")
