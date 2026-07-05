import os
import sys
import stat

def install_pre_commit_hook():
    """Finds the local hidden .git/hooks directory and writes a pre-commit shell script."""
    # Find the path of the 'agents' directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(current_dir))
    
    git_hooks_dir = os.path.join(project_root, ".git", "hooks")
    
    if not os.path.exists(git_hooks_dir):
        print("❌ Error: Target is not a verified Git repository or root folder is detached.")
        return False

    hook_path = os.path.join(git_hooks_dir, "pre-commit")
    
    # Write the script contents that Git will execute during a commit lifecycle
    hook_content = f"""#!/bin/sh
echo "🔍 Running Code Quality Agent Pre-Commit Automated Gate..."
export PYTHONPATH="{project_root}"

# Trigger the CLI engine against the current working directory
python -m person_2 .

# Check the exit status code of our scan engine
if [ $? -ne 0 ]; then
    echo "❌ Commit Blocked: Code Quality Agent discovered structural or smell anomalies."
    exit 1
fi

echo "✅ Quality check passed. Proceeding with commit."
exit 0
"""

    try:
        with open(hook_path, "w", newline="\n", encoding="utf-8") as f:
            f.write(hook_content)
        
        # Give the script executable permissions (crucial for Linux/Git Bash setups)
        st = os.stat(hook_path)
        os.chmod(hook_path, st.st_mode | stat.S_IEXEC)
        
        print(f"🎯 Pre-commit hook successfully installed at: {hook_path}")
        return True
    except Exception as e:
        print(f"❌ Failed to write automated hook mapping: {str(e)}")
        return False

if __name__ == "__main__":
    install_pre_commit_hook()