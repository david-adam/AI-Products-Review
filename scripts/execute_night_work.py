#!/usr/bin/env python3
"""
Autonomous Night Work Executor

Reads NIGHTLY_TODOS.md and executes pending tasks dynamically.
"""

import os
import re
import subprocess
from datetime import datetime

WORKSPACE = "/Users/trinitym/.openclaw/workspace-coder-fast/scraper_api"
TODOS_FILE = f"{WORKSPACE}/NIGHTLY_TODOS.md"
PROGRESS_FILE = f"{WORKSPACE}/NIGHTLY_PROGRESS.md"


def parse_todos():
    """
    Parse NIGHTLY_TODOS.md to extract pending tasks.
    
    Returns:
        list: Pending tasks with metadata
    """
    if not os.path.exists(TODOS_FILE):
        log("❌ NIGHTLY_TODOS.md not found!")
        return []
    
    with open(TODOS_FILE, 'r') as f:
        content = f.read()
    
    # Find unchecked tasks (checkboxes with "- [ ]")
    tasks = []
    current_section = "General"
    
    for line in content.split('\n'):
        # Track sections
        if line.startswith('## '):
            current_section = line.replace('## ', '').strip()
        
        # Find unchecked tasks
        if '- [ ]' in line:
            task = line.replace('- [ ]', '').strip()
            # Remove bold markdown
            task = re.sub(r'\*\*(.*?)\*\*', r'\1', task)
            
            tasks.append({
                'title': task,
                'section': current_section,
                'line': line
            })
    
    return tasks


def execute_task(task):
    """
    Execute a task by delegating to appropriate handler.
    
    Args:
        task (dict): Task information
    
    Returns:
        bool: Success status
    """
    title = task['title'].lower()
    section = task['section']
    
    log(f"🔄 Executing: {task['title']}")
    log(f"   Section: {section}")
    
    # Route to appropriate handler based on task keywords
    if 'database' in title and 'deploy' in title:
        return deploy_database_schema(task)
    elif 'test' in title and 'database' in title:
        return test_database_integration(task)
    elif 'generate' in title and 'content' in title:
        return generate_content_samples(task)
    elif 'vercel' in title or 'api' in title:
        return update_vercel_api(task)
    else:
        log(f"⚠️  No handler for: {task['title']}")
        log(f"   Task queued for morning review")
        return False


def deploy_database_schema(task):
    """Deploy database schema to Turso."""
    log("   📂 Deploying schema to Turso...")
    
    try:
        # Run migration script
        result = subprocess.run(
            ['python3', 'scripts/db_integration_simple.py'],
            cwd=WORKSPACE,
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode == 0:
            log("   ✅ Schema deployed successfully")
            mark_task_complete(task)
            return True
        else:
            log(f"   ❌ Deployment failed: {result.stderr}")
            return False
    
    except Exception as e:
        log(f"   ❌ Error: {e}")
        return False


def test_database_integration(task):
    """Test database integration."""
    log("   🧪 Testing database integration...")
    
    try:
        result = subprocess.run(
            ['python3', 'scripts/db_integration_simple.py'],
            cwd=WORKSPACE,
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode == 0:
            log("   ✅ Integration test passed")
            mark_task_complete(task)
            return True
        else:
            log(f"   ❌ Test failed: {result.stderr}")
            return False
    
    except Exception as e:
        log(f"   ❌ Error: {e}")
        return False


def generate_content_samples(task):
    """Generate content samples."""
    log("   🎨 Generating content samples...")
    
    try:
        result = subprocess.run(
            ['python3', 'test_ai_pipeline.py'],
            cwd=WORKSPACE,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode == 0:
            log("   ✅ Content generated successfully")
            mark_task_complete(task)
            return True
        else:
            log(f"   ❌ Generation failed: {result.stderr}")
            return False
    
    except Exception as e:
        log(f"   ❌ Error: {e}")
        return False


def update_vercel_api(task):
    """Update Vercel API endpoints."""
    log("   ⚠️  Vercel updates require user approval")
    log("   Task queued for morning")
    return False


def mark_task_complete(task):
    """Mark a task as complete in NIGHTLY_TODOS.md."""
    try:
        with open(TODOS_FILE, 'r') as f:
            content = f.read()
        
        # Replace "- [ ]" with "- [x]" for this task
        old_line = task['line']
        new_line = old_line.replace('- [ ]', '- [x]')
        
        content = content.replace(old_line, new_line)
        
        with open(TODOS_FILE, 'w') as f:
            f.write(content)
        
        log("   ✅ Marked complete in NIGHTLY_TODOS.md")
    
    except Exception as e:
        log(f"   ⚠️  Could not mark complete: {e}")


def log(message):
    """Log to progress file and stdout."""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_line = f"[{timestamp}] {message}"
    
    print(log_line)
    
    with open(PROGRESS_FILE, 'a') as f:
        f.write(log_line + '\n')


def main():
    """Main execution."""
    log("=" * 70)
    log("🌙 AUTONOMOUS NIGHT WORK STARTED")
    log("=" * 70)
    
    # Parse pending tasks
    tasks = parse_todos()
    
    if not tasks:
        log("📭 No pending tasks found in NIGHTLY_TODOS.md")
        log("   Going back to sleep...")
        return
    
    log(f"📋 Found {len(tasks)} pending tasks")
    log()
    
    # Execute tasks in priority order
    completed = 0
    failed = 0
    
    for task in tasks:
        if execute_task(task):
            completed += 1
        else:
            failed += 1
        
        log()
    
    # Summary
    log("=" * 70)
    log("🌙 NIGHT WORK COMPLETE")
    log("=" * 70)
    log(f"✅ Completed: {completed}")
    log(f"❌ Failed: {failed}")
    log(f"⏳ Pending: {len(tasks) - completed - failed}")
    log()
    log("📄 See NIGHTLY_PROGRESS.md for details")
    log("🌅 Morning report will be sent at 06:30")


if __name__ == "__main__":
    main()
