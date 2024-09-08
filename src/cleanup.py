import os
import shutil

def cleanup_temp_files():
    # Directory where temporary files are stored
    temp_dir = "temp"
    
    # Check if temp directory exists
    if not os.path.exists(temp_dir):
        print("No temporary files to clean up.")
        return

    # List all files in the temp directory
    temp_files = os.listdir(temp_dir)
    
    # Separate HTML files and other temp files
    html_files = [f for f in temp_files if f.endswith('.html')]
    other_temp_files = [f for f in temp_files if not f.endswith('.html')]
    
    # Ask user about HTML files
    for html_file in html_files:
        save = input(f"Do you want to save {html_file} before deleting? (y/n): ").lower() == 'y'
        if save:
            new_name = input(f"Enter new name for {html_file}: ")
            shutil.move(os.path.join(temp_dir, html_file), new_name)
        else:
            os.remove(os.path.join(temp_dir, html_file))
    
    # Delete other temporary files
    for temp_file in other_temp_files:
        os.remove(os.path.join(temp_dir, temp_file))
    
    # Remove the temp directory if it's empty
    if not os.listdir(temp_dir):
        os.rmdir(temp_dir)
    
    print("Cleanup completed.")

if __name__ == "__main__":
    cleanup_temp_files()