# git_auto_upload.py
import os
import subprocess
from datetime import datetime

# === GitHub Auto Upload Script ===
# Run this file to automatically add, commit, and push all changes to GitHub

# Optional: Custom commit message with timestamp
commit_message = f"Auto update on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

try:
    # Step 1: Git Add
    subprocess.run(["git", "add", "."], check=True)

    # Step 2: Git Commit
    subprocess.run(["git", "commit", "-m", commit_message], check=True)

    # Step 3: Git Push
    subprocess.run(["git", "push"], check=True)

    print("\n✅ Successfully uploaded changes to GitHub!")
except subprocess.CalledProcessError as e:
    print("\n❌ Git command failed. Details:")
    print(e)
except Exception as ex:
    print("\n❌ Unexpected error:")
    print(ex)