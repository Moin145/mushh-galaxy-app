#!/usr/bin/env python3
"""
Deployment Helper Script for Mushh's Galaxy App
"""

import os
import subprocess
import sys

def run_command(command):
    """Run a command and return the result"""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def check_git():
    """Check if git is available and initialized"""
    success, stdout, stderr = run_command("git --version")
    if not success:
        print("❌ Git is not installed. Please install Git first.")
        return False
    
    success, stdout, stderr = run_command("git status")
    if not success:
        print("❌ Git repository not initialized. Initializing...")
        success, stdout, stderr = run_command("git init")
        if not success:
            print("❌ Failed to initialize git repository")
            return False
    
    return True

def create_gitignore():
    """Create .gitignore file if it doesn't exist"""
    gitignore_content = """
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
venv/
env/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs
*.log

# Environment variables
.env
.env.local

# Temporary files
*.tmp
*.temp
"""
    
    if not os.path.exists('.gitignore'):
        with open('.gitignore', 'w') as f:
            f.write(gitignore_content)
        print("✅ Created .gitignore file")

def main():
    print("🚀 Mushh's Galaxy App - Deployment Helper")
    print("=" * 50)
    
    # Check git
    if not check_git():
        return
    
    # Create .gitignore
    create_gitignore()
    
    # Add all files
    print("📁 Adding files to git...")
    success, stdout, stderr = run_command("git add .")
    if not success:
        print("❌ Failed to add files to git")
        return
    
    # Commit
    print("💾 Committing changes...")
    success, stdout, stderr = run_command('git commit -m "Ready for deployment"')
    if not success:
        print("❌ Failed to commit changes")
        return
    
    print("✅ Git repository is ready!")
    print("\n🎯 Next Steps:")
    print("1. Create a GitHub repository at https://github.com/new")
    print("2. Push your code to GitHub:")
    print("   git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git")
    print("   git push -u origin main")
    print("3. Deploy to Render:")
    print("   - Go to https://render.com")
    print("   - Sign up and connect your GitHub account")
    print("   - Create a new Web Service")
    print("   - Select your repository")
    print("   - Deploy!")
    print("\n📖 For detailed instructions, see DEPLOYMENT.md")

if __name__ == "__main__":
    main() 