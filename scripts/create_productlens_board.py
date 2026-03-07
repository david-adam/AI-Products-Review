#!/usr/bin/env python3
"""
Recreate TaskFlow Board - Project-Based Design

Correct design: One board per project, tasks can be worked on anytime (day or night).
Cronjob checks ALL boards for cards in "To Do" or "In Progress".
"""

import json
from datetime import datetime

TASKFLOW_DB = "/Users/trinitym/.openclaw/workspace/trello-clone/taskflow.db"
USER_ID = "1770958266694"  # TrinityM
TEAM_ID = "1770958266625"  # Amazon Affiliate team


def recreate_productlens_board():
    """Recreate the ProductLens AI board with correct structure."""
    
    # Load existing data
    with open(TASKFLOW_DB, 'r') as f:
        data = json.load(f)
    
    # Remove the old "Night Work" board if it exists
    data['boards'] = [b for b in data['boards'] if 'Night Work' not in b['name']]
    old_board_ids = [b['id'] for b in data['boards'] if 'Night Work' in b['name']]
    
    # Remove associated lists and cards
    if old_board_ids:
        data['lists'] = [l for l in data['lists'] if l['boardId'] not in old_board_ids]
        data['cards'] = [c for c in data['cards'] if c.get('boardId') not in old_board_ids]
    
    # Generate unique IDs
    timestamp = int(datetime.now().timestamp() * 1000)
    board_id = f"productlens_board_{timestamp}"
    
    # Create ProductLens AI board
    new_board = {
        "id": board_id,
        "name": "ProductLens AI",
        "teamId": TEAM_ID,
        "createdBy": USER_ID,
        "createdAt": datetime.now().isoformat() + "Z"
    }
    
    data["boards"].append(new_board)
    
    # Create standard lists (Trello-style)
    lists = [
        {
            "id": f"pl_list_backlog_{timestamp}",
            "name": "Backlog",
            "boardId": board_id,
            "position": 0,
            "createdAt": datetime.now().isoformat() + "Z"
        },
        {
            "id": f"pl_list_todo_{timestamp}",
            "name": "To Do",
            "boardId": board_id,
            "position": 1,
            "createdAt": datetime.now().isoformat() + "Z"
        },
        {
            "id": f"pl_list_progress_{timestamp}",
            "name": "In Progress",
            "boardId": board_id,
            "position": 2,
            "createdAt": datetime.now().isoformat() + "Z"
        },
        {
            "id": f"pl_list_review_{timestamp}",
            "name": "Review",
            "boardId": board_id,
            "position": 3,
            "createdAt": datetime.now().isoformat() + "Z"
        },
        {
            "id": f"pl_list_done_{timestamp}",
            "name": "Done",
            "boardId": board_id,
            "position": 4,
            "createdAt": datetime.now().isoformat() + "Z"
        }
    ]
    
    data["lists"].extend(lists)
    
    # Get list IDs
    todo_list_id = lists[1]["id"]  # "To Do"
    progress_list_id = lists[2]["id"]  # "In Progress"
    
    # Create initial cards from Phase 2 tasks
    initial_cards = [
        {
            "id": f"pl_card_deploy_{timestamp}",
            "title": "Deploy Database Schema to Turso",
            "description": "Run migrations.sql on Turso DB, verify all 5 tables created\n\n**Priority:** P0\n**Time Estimate:** 30 minutes",
            "listId": todo_list_id,
            "position": 0,
            "labels": ["P0", "Database"],
            "createdAt": datetime.now().isoformat() + "Z"
        },
        {
            "id": f"pl_card_test_{timestamp}",
            "title": "Test Database Integration",
            "description": "Run db_integration_simple.py, fetch products, save test review\n\n**Priority:** P0\n**Time Estimate:** 30 minutes\n**Dependencies:** Schema deployed",
            "listId": todo_list_id,
            "position": 1,
            "labels": ["P0", "Database", "Testing"],
            "createdAt": datetime.now().isoformat() + "Z"
        },
        {
            "id": f"pl_card_samples_{timestamp}",
            "title": "Generate Content Samples for Review",
            "description": "Pick 3-5 products, generate summaries + full reviews, create social images, upload to Google Drive\n\n**Priority:** P0\n**Time Estimate:** 45 minutes\n**Dependencies:** DB integration working",
            "listId": todo_list_id,
            "position": 2,
            "labels": ["P0", "AI", "Content"],
            "createdAt": datetime.now().isoformat() + "Z"
        },
        {
            "id": f"pl_card_vercel_{timestamp}",
            "title": "Update Vercel API Endpoints",
            "description": "Create api/reviews.js endpoint, add queries for new tables, test locally\n\n**Priority:** P1\n**Time Estimate:** 1 hour\n**Dependencies:** Schema deployed",
            "listId": todo_list_id,
            "position": 3,
            "labels": ["P1", "API", "Vercel"],
            "createdAt": datetime.now().isoformat() + "Z"
        },
        {
            "id": f"pl_card_dashboard_{timestamp}",
            "title": "Create Content Generation Dashboard",
            "description": "Admin page to view generated content, show pending/published counts, add manual trigger button\n\n**Priority:** P1\n**Time Estimate:** 1.5 hours",
            "listId": todo_list_id,
            "position": 4,
            "labels": ["P1", "UI", "Dashboard"],
            "createdAt": datetime.now().isoformat() + "Z"
        },
        {
            "id": f"pl_card_cron_{timestamp}",
            "title": "Set Up Daily Cron Job",
            "description": "Configure cron job for daily content generation at 7 AM Shanghai time\n\n**Priority:** P2\n**Time Estimate:** 30 minutes",
            "listId": todo_list_id,
            "position": 5,
            "labels": ["P2", "DevOps"],
            "createdAt": datetime.now().isoformat() + "Z"
        }
    ]
    
    data["cards"].extend(initial_cards)
    
    # Save back to file
    with open(TASKFLOW_DB, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"✅ Created 'ProductLens AI' board!")
    print(f"   Board ID: {board_id}")
    print(f"   Lists: 5 (Backlog, To Do, In Progress, Review, Done)")
    print(f"   Cards: {len(initial_cards)}")
    print()
    print("📋 Initial Tasks (all in 'To Do'):")
    for card in initial_cards:
        labels = ', '.join(card.get('labels', []))
        print(f"   [{labels}] {card['title']}")
    
    return board_id


if __name__ == "__main__":
    recreate_productlens_board()
