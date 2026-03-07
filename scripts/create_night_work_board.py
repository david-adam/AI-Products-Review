#!/usr/bin/env python3
"""
Create Night Work Board in TaskFlow

Adds a new board with lists for autonomous night work tasks.
"""

import json
from datetime import datetime

TASKFLOW_DB = "/Users/trinitym/.openclaw/workspace/trello-clone/taskflow.db"
USER_ID = "1770958266694"  # TrinityM
TEAM_ID = "1770958266625"  # Amazon Affiliate team


def create_night_work_board():
    """Create the Night Work board in TaskFlow."""
    
    # Load existing data
    with open(TASKFLOW_DB, 'r') as f:
        data = json.load(f)
    
    # Generate unique IDs
    timestamp = int(datetime.now().timestamp() * 1000)
    board_id = f"night_board_{timestamp}"
    
    # Create board
    new_board = {
        "id": board_id,
        "name": "Night Work - Autonomous Tasks",
        "teamId": TEAM_ID,
        "createdBy": USER_ID,
        "createdAt": datetime.now().isoformat() + "Z"
    }
    
    data["boards"].append(new_board)
    
    # Create lists
    lists = [
        {
            "id": f"night_list_tonight_{timestamp}",
            "name": "🌙 Tonight",
            "boardId": board_id,
            "position": 0,
            "createdAt": datetime.now().isoformat() + "Z"
        },
        {
            "id": f"night_list_progress_{timestamp}",
            "name": "🔄 In Progress",
            "boardId": board_id,
            "position": 1,
            "createdAt": datetime.now().isoformat() + "Z"
        },
        {
            "id": f"night_list_done_{timestamp}",
            "name": "✅ Done",
            "boardId": board_id,
            "position": 2,
            "createdAt": datetime.now().isoformat() + "Z"
        },
        {
            "id": f"night_list_blocked_{timestamp}",
            "name": "⏸️ Blocked",
            "boardId": board_id,
            "position": 3,
            "createdAt": datetime.now().isoformat() + "Z"
        },
        {
            "id": f"night_list_daytime_{timestamp}",
            "name": "☀️ Daytime",
            "boardId": board_id,
            "position": 4,
            "createdAt": datetime.now().isoformat() + "Z"
        }
    ]
    
    data["lists"].extend(lists)
    
    # Create initial cards from NIGHTLY_TODOS.md
    tonight_list_id = lists[0]["id"]
    
    initial_cards = [
        {
            "id": f"night_card_deploy_{timestamp}",
            "title": "Deploy Database Schema to Turso",
            "description": "Run migrations.sql on Turso DB, verify all 5 tables created. Priority: P0",
            "listId": tonight_list_id,
            "position": 0,
            "labels": ["P0"],
            "createdAt": datetime.now().isoformat() + "Z"
        },
        {
            "id": f"night_card_test_{timestamp}",
            "title": "Test Database Integration",
            "description": "Run db_integration_simple.py, fetch products, save test review. Priority: P0",
            "listId": tonight_list_id,
            "position": 1,
            "labels": ["P0"],
            "createdAt": datetime.now().isoformat() + "Z"
        },
        {
            "id": f"night_card_samples_{timestamp}",
            "title": "Generate Content Samples",
            "description": "Pick 3-5 products, generate summaries + full reviews, create social images. Priority: P0",
            "listId": tonight_list_id,
            "position": 2,
            "labels": ["P0"],
            "createdAt": datetime.now().isoformat() + "Z"
        },
        {
            "id": f"night_card_vercel_{timestamp}",
            "title": "Update Vercel API Endpoints",
            "description": "Create api/reviews.js endpoint, add queries for new tables. Priority: P1",
            "listId": tonight_list_id,
            "position": 3,
            "labels": ["P1"],
            "createdAt": datetime.now().isoformat() + "Z"
        },
        {
            "id": f"night_card_dashboard_{timestamp}",
            "title": "Create Content Generation Dashboard",
            "description": "Admin page to view generated content, add manual trigger. Priority: P1",
            "listId": tonight_list_id,
            "position": 4,
            "labels": ["P1"],
            "createdAt": datetime.now().isoformat() + "Z"
        }
    ]
    
    data["cards"].extend(initial_cards)
    
    # Save back to file
    with open(TASKFLOW_DB, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"✅ Created 'Night Work - Autonomous Tasks' board!")
    print(f"   Board ID: {board_id}")
    print(f"   Lists: 5 (Tonight, In Progress, Done, Blocked, Daytime)")
    print(f"   Cards: {len(initial_cards)}")
    print()
    print("📋 Initial Tasks:")
    for card in initial_cards:
        label = card['labels'][0] if card.get('labels') else ''
        print(f"   [{label}] {card['title']}")
    
    return board_id


if __name__ == "__main__":
    create_night_work_board()
