#!/usr/bin/env python3
"""
TaskFlow Autonomous Work Executor

Checks ALL project boards for cards in "To Do" or "In Progress" and executes them.
Can work 24/7 (daytime and nighttime) on any project.
"""

import json
import subprocess
from datetime import datetime

TASKFLOW_DB = "/Users/trinitym/.openclaw/workspace/trello-clone/taskflow.db"
WORKSPACE = "/Users/trinitym/.openclaw/workspace/coder-fast/scraper_api"


def load_taskflow():
    """Load TaskFlow database."""
    with open(TASKFLOW_DB, 'r') as f:
        return json.load(f)


def save_taskflow(data):
    """Save TaskFlow database."""
    with open(TASKFLOW_DB, 'w') as f:
        json.dump(data, f, indent=2)


def log(message):
    """Log to stdout and file."""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_line = f"[{timestamp}] {message}"
    
    print(log_line)
    
    # Log to workspace-specific progress file
    import os
    workspace_progress = f"{WORKSPACE}/AUTONOMOUS_WORK_PROGRESS.md"
    with open(workspace_progress, 'a') as f:
        f.write(log_line + '\n')


def get_list_by_name(data, board_id, list_name):
    """Get a list by name for a specific board."""
    for lst in data['lists']:
        if lst['boardId'] == board_id and lst['name'] == list_name:
            return lst
    return None


def get_cards_in_lists(data, board_id, list_names):
    """Get all cards in specified lists for a board."""
    list_ids = [lst['id'] for lst in data['lists'] 
                if lst['boardId'] == board_id and lst['name'] in list_names]
    
    cards = []
    for list_id in list_ids:
        cards.extend([c for c in data['cards'] if c['listId'] == list_id])
    
    # Sort by position
    return sorted(cards, key=lambda c: c.get('position', 0))


def move_card(data, card, to_list_name, board_id):
    """Move a card to a different list."""
    to_list = get_list_by_name(data, board_id, to_list_name)
    if not to_list:
        return False
    
    card['listId'] = to_list['id']
    return True


def add_comment_to_card(card, comment):
    """Add a comment to a card."""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    separator = "\n\n---\n\n"
    
    if 'comments' not in card:
        card['comments'] = []
    
    card['comments'].append({
        'timestamp': timestamp,
        'text': comment
    })
    
    # Also append to description for visibility
    card['description'] = card.get('description', '') + separator + f"**{timestamp}**\n{comment}"


def execute_task(card, board_name, data, board_id):
    """Execute a single task."""
    title = card['title']
    description = card.get('description', '')
    labels = card.get('labels', [])
    
    log(f"🔄 [{board_name}] {title}")
    log(f"   Labels: {', '.join(labels) if labels else 'None'}")
    
    # Determine task type and route to handler
    title_lower = title.lower()
    
    try:
        # Database tasks
        if 'database' in title_lower and 'deploy' in title_lower:
            success = deploy_database_schema(card)
        elif 'test' in title_lower and 'database' in title_lower:
            success = test_database_integration(card)
        
        # Content generation tasks
        elif 'generate' in title_lower and 'content' in title_lower:
            success = generate_content_samples(card)
        
        # API/Vercel tasks (require approval)
        elif 'vercel' in title_lower or 'api' in title_lower:
            success = update_vercel_api(card)
        
        # UI tasks (need user input)
        elif 'dashboard' in title_lower:
            success = create_dashboard(card)
        
        # DevOps tasks
        elif 'cron' in title_lower:
            success = setup_cron(card)
        
        else:
            log(f"   ⚠️  No handler for this task type")
            log(f"   Moving to 'Review' for manual handling")
            move_card(data, card, 'Review', board_id)
            add_comment_to_card(card, "⚠️ No automated handler available. Needs manual execution or handler implementation.")
            return False
        
        if success:
            log(f"   ✅ Task completed successfully")
            move_card(data, card, 'Done', board_id)
            add_comment_to_card(card, f"✅ Completed by autonomous worker at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            log(f"   ❌ Task failed")
            move_card(data, card, 'Review', board_id)
            add_comment_to_card(card, f"❌ Failed during autonomous execution. Check AUTONOMOUS_WORK_PROGRESS.md for details.")
        
        return success
    
    except Exception as e:
        log(f"   ❌ Error: {e}")
        move_card(data, card, 'Review', board_id)
        add_comment_to_card(card, f"❌ Exception: {str(e)}")
        return False


def deploy_database_schema(card):
    """Deploy database schema."""
    log("   📂 Deploying schema to Turso...")
    
    result = subprocess.run(
        ['python3', 'scripts/db_integration_simple.py'],
        cwd=WORKSPACE,
        capture_output=True,
        text=True,
        timeout=120
    )
    
    if result.returncode == 0:
        log("   ✓ Schema deployed")
        add_comment_to_card(card, "Output:\n" + result.stdout[-500:])
        return True
    else:
        log(f"   ✗ Failed: {result.stderr[-200:]}")
        add_comment_to_card(card, "Error:\n" + result.stderr[-500:])
        return False


def test_database_integration(card):
    """Test database integration."""
    log("   🧪 Testing database integration...")
    
    result = subprocess.run(
        ['python3', 'scripts/db_integration_simple.py'],
        cwd=WORKSPACE,
        capture_output=True,
        text=True,
        timeout=120
    )
    
    if result.returncode == 0:
        log("   ✓ Integration test passed")
        add_comment_to_card(card, "Output:\n" + result.stdout[-500:])
        return True
    else:
        log(f"   ✗ Failed: {result.stderr[-200:]}")
        add_comment_to_card(card, "Error:\n" + result.stderr[-500:])
        return False


def generate_content_samples(card):
    """Generate content samples."""
    log("   🎨 Generating content samples...")
    
    result = subprocess.run(
        ['python3', 'test_ai_pipeline.py'],
        cwd=WORKSPACE,
        capture_output=True,
        text=True,
        timeout=300
    )
    
    if result.returncode == 0:
        log("   ✓ Content generated")
        add_comment_to_card(card, "Output:\n" + result.stdout[-500:])
        return True
    else:
        log(f"   ✗ Failed: {result.stderr[-200:]}")
        add_comment_to_card(card, "Error:\n" + result.stderr[-500:])
        return False


def update_vercel_api(card):
    """Update Vercel API (requires approval)."""
    log("   ⚠️  Vercel deployment requires user approval")
    add_comment_to_card(card, "⚠️ This task requires user approval before deployment. Moved to Review for your attention.")
    return False


def create_dashboard(card):
    """Create dashboard."""
    log("   ⚠️  Dashboard creation needs user input on design")
    add_comment_to_card(card, "⚠️ Dashboard design needs user input. Moved to Review for your decision.")
    return False


def setup_cron(card):
    """Setup cron job."""
    log("   ⚙️ Setting up cron job...")
    
    result = subprocess.run(
        ['./scripts/install_taskflow_cron.sh'],
        cwd=WORKSPACE,
        capture_output=True,
        text=True,
        timeout=60
    )
    
    if result.returncode == 0:
        log("   ✓ Cron job installed")
        add_comment_to_card(card, "Output:\n" + result.stdout[-500:])
        return True
    else:
        log(f"   ✗ Failed: {result.stderr[-200:]}")
        add_comment_to_card(card, "Error:\n" + result.stderr[-500:])
        return False


def main():
    """Main execution."""
    log("=" * 70)
    log("🤖 TASKFLOW AUTONOMOUS WORK EXECUTOR")
    log("=" * 70)
    
    # Load TaskFlow
    data = load_taskflow()
    
    # Get all boards
    boards = data['boards']
    
    if not boards:
        log("❌ No boards found in TaskFlow!")
        return
    
    log(f"📊 Found {len(boards)} project board(s)")
    
    total_cards = 0
    total_completed = 0
    total_failed = 0
    
    # Process each board
    for board in boards:
        board_name = board['name']
        board_id = board['id']
        
        # Get cards in "To Do" and "In Progress"
        cards = get_cards_in_lists(data, board_id, ['To Do', 'In Progress'])
        
        if not cards:
            log(f"   📭 [{board_name}] No actionable tasks")
            continue
        
        log(f"   📋 [{board_name}] Found {len(cards)} task(s)")
        total_cards += len(cards)
        
        # Execute each card
        for card in cards:
            if execute_task(card, board_name, data, board_id):
                total_completed += 1
            else:
                total_failed += 1
            
            log()
    
    # Save updated state
    save_taskflow(data)
    log("💾 TaskFlow boards updated")
    
    # Summary
    log("=" * 70)
    log("🤖 EXECUTION COMPLETE")
    log("=" * 70)
    log(f"📊 Total tasks found: {total_cards}")
    log(f"✅ Completed: {total_completed}")
    log(f"❌ Failed: {total_failed}")
    log(f"⏸️ Pending: {total_cards - total_completed - total_failed}")
    log()
    log(f"📁 Progress log: {WORKSPACE}/AUTONOMOUS_WORK_PROGRESS.md")
    log(f"📊 Check TaskFlow boards for updated card positions")


if __name__ == "__main__":
    main()
