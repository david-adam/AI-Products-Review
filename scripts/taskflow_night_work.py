#!/usr/bin/env python3
"""
TaskFlow Night Work Executor

Reads from TaskFlow "Night Work" board and executes pending tasks.
"""

import json
import subprocess
import sys
from datetime import datetime

TASKFLOW_DB = "/Users/trinitym/.openclaw/workspace/trello-clone/taskflow.db"
WORKSPACE = "/Users/trinitym/.openclaw/workspace-coder-fast/scraper_api"


def load_taskflow():
    """Load TaskFlow database."""
    with open(TASKFLOW_DB, 'r') as f:
        return json.load(f)


def save_taskflow(data):
    """Save TaskFlow database."""
    with open(TASKFLOW_DB, 'w') as f:
        json.dump(data, f, indent=2)


def get_night_work_board(data):
    """Get the Night Work board."""
    for board in data['boards']:
        if 'Night Work' in board['name']:
            return board
    return None


def get_lists_by_name(data, board_id):
    """Get lists indexed by name for a board."""
    lists_by_name = {}
    for lst in data['lists']:
        if lst['boardId'] == board_id:
            lists_by_name[lst['name']] = lst
    return lists_by_name


def get_cards_in_list(data, list_id):
    """Get all cards in a list, sorted by position."""
    cards = [c for c in data['cards'] if c['listId'] == list_id]
    return sorted(cards, key=lambda c: c.get('position', 0))


def move_card(data, card, to_list_name, lists_by_name):
    """Move a card to a different list."""
    to_list = lists_by_name.get(to_list_name)
    if not to_list:
        return False
    
    card['listId'] = to_list['id']
    return True


def add_comment_to_card(card, comment):
    """Add a comment to a card (stored in description for now)."""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    separator = "\n\n---\n\n"
    
    if 'comments' not in card:
        card['comments'] = []
    
    card['comments'].append({
        'timestamp': timestamp,
        'text': comment
    })
    
    # Also append to description for visibility in TaskFlow
    card['description'] = card.get('description', '') + separator + f"**{timestamp}**\n{comment}"


def log(message):
    """Log to stdout and file."""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_line = f"[{timestamp}] {message}"
    
    print(log_line)
    
    with open(f'{WORKSPACE}/NIGHTLY_PROGRESS.md', 'a') as f:
        f.write(log_line + '\n')


def execute_task(card, lists_by_name):
    """Execute a single task."""
    title = card['title']
    description = card.get('description', '')
    labels = card.get('labels', [])
    
    log(f"🔄 Executing: {title}")
    log(f"   Priority: {labels[0] if labels else 'None'}")
    
    # Determine task type and route to appropriate handler
    title_lower = title.lower()
    
    try:
        if 'database' in title_lower and 'deploy' in title_lower:
            success = deploy_database_schema(card)
        elif 'test' in title_lower and 'database' in title_lower:
            success = test_database_integration(card)
        elif 'generate' in title_lower and 'content' in title_lower:
            success = generate_content_samples(card)
        elif 'vercel' in title_lower or 'api' in title_lower:
            success = update_vercel_api(card)
        elif 'dashboard' in title_lower:
            success = create_dashboard(card)
        else:
            log(f"   ⚠️  No handler for this task type")
            log(f"   Task moved to '⏸️ Blocked' for review")
            move_card(data, card, '⏸️ Blocked', lists_by_name)
            add_comment_to_card(card, "No automated handler available. Needs manual execution.")
            return False
        
        if success:
            log(f"   ✅ Task completed successfully")
            move_card(data, card, '✅ Done', lists_by_name)
            add_comment_to_card(card, f"✅ Completed by autonomous night work at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            log(f"   ❌ Task failed")
            move_card(data, card, '⏸️ Blocked', lists_by_name)
            add_comment_to_card(card, f"❌ Failed during autonomous night work. Check NIGHTLY_PROGRESS.md for details.")
        
        return success
    
    except Exception as e:
        log(f"   ❌ Error: {e}")
        move_card(data, card, '⏸️ Blocked', lists_by_name)
        add_comment_to_card(card, f"❌ Error: {str(e)}")
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
        add_comment_to_card(card, "Schema deployment output:\n" + result.stdout[-500:])
        return True
    else:
        log(f"   ✗ Failed: {result.stderr[-200:]}")
        add_comment_to_card(card, "Schema deployment error:\n" + result.stderr[-500:])
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
        add_comment_to_card(card, "Test output:\n" + result.stdout[-500:])
        return True
    else:
        log(f"   ✗ Failed: {result.stderr[-200:]}")
        add_comment_to_card(card, "Test error:\n" + result.stderr[-500:])
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
        add_comment_to_card(card, "Generation output:\n" + result.stdout[-500:])
        return True
    else:
        log(f"   ✗ Failed: {result.stderr[-200:]}")
        add_comment_to_card(card, "Generation error:\n" + result.stderr[-500:])
        return False


def update_vercel_api(card):
    """Update Vercel API (requires approval)."""
    log("   ⚠️  Vercel deployment requires user approval")
    add_comment_to_card(card, "⚠️ This task requires user approval before deployment. Moved to Blocked for review.")
    return False


def create_dashboard(card):
    """Create dashboard."""
    log("   ⚠️  Dashboard creation needs user input on design")
    add_comment_to_card(card, "⚠️ Dashboard design needs user input. Moved to Blocked for review.")
    return False


def main():
    """Main execution."""
    log("=" * 70)
    log("🌙 TASKFLOW AUTONOMOUS NIGHT WORK")
    log("=" * 70)
    
    # Load TaskFlow
    data = load_taskflow()
    
    # Get Night Work board
    board = get_night_work_board(data)
    if not board:
        log("❌ 'Night Work' board not found!")
        return
    
    log(f"📋 Board: {board['name']}")
    
    # Get lists
    lists_by_name = get_lists_by_name(data, board['id'])
    
    # Get cards in "Tonight" list
    tonight_list = lists_by_name.get('🌙 Tonight')
    if not tonight_list:
        log("❌ 'Tonight' list not found!")
        return
    
    cards = get_cards_in_list(data, tonight_list['id'])
    
    if not cards:
        log("📭 No tasks in 'Tonight' list")
        log("   Going back to sleep...")
        return
    
    log(f"📊 Found {len(cards)} tasks to execute")
    log()
    
    # Execute tasks
    completed = 0
    failed = 0
    
    for card in cards:
        if execute_task(card, lists_by_name):
            completed += 1
        else:
            failed += 1
        
        log()
    
    # Save updated TaskFlow state
    save_taskflow(data)
    log("💾 TaskFlow board updated")
    
    # Summary
    log("=" * 70)
    log("🌙 NIGHT WORK COMPLETE")
    log("=" * 70)
    log(f"✅ Completed: {completed}")
    log(f"❌ Failed: {failed}")
    log(f"⏸️ Blocked: {len(cards) - completed - failed}")
    log()
    log(f"📊 Check TaskFlow board for updated card positions")


if __name__ == "__main__":
    main()
