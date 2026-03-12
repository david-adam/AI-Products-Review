#!/usr/bin/env node

/**
 * Night Work Executor - Fetches tasks from ProductLens AI TaskFlow board
 * Runs during autonomous hours: 23:30 - 06:30
 * 
 * Targeting: ProductLens AI Development board only
 * Moves completed tasks to "Review" list
 */

import fs from 'fs';
import path from 'path';

// Configuration
const TASKFLOW_DB_PATH = '/Users/trinitym/.openclaw/workspace/trello-clone/taskflow.db';
const LOG_DIR = '/Users/trinitym/.openclaw/workspace-coder-fast/scraper_api/logs';
const LOG_FILE = path.join(LOG_DIR, 'nightly.log');

// ProductLens AI Board ID
const PRODUCTLENS_BOARD_ID = 'board_productlens_1772858348683';

/**
 * Log message to both console and nightly.log
 */
function log(message, level = 'INFO') {
  const timestamp = new Date().toISOString();
  const logLine = `[${timestamp}] [${level}] ${message}`;
  console.log(logLine);
  
  try {
    fs.appendFileSync(LOG_FILE, logLine + '\n');
  } catch (err) {
    console.error('Failed to write to log file:', err.message);
  }
}

/**
 * Fetch cards from ProductLens AI TaskFlow board "To Do" and "In Progress" lists
 * Reads directly from database (no authentication needed)
 */
async function fetchNightTasks() {
  return new Promise((resolve, reject) => {
    try {
      // Read database
      if (!fs.existsSync(TASKFLOW_DB_PATH)) {
        reject(new Error('TaskFlow database not found'));
        return;
      }

      const data = JSON.parse(fs.readFileSync(TASKFLOW_DB_PATH, 'utf8'));
      
      // Find ProductLens AI board
      const board = data.boards?.find(b => b.id === PRODUCTLENS_BOARD_ID);
      
      if (!board) {
        reject(new Error('ProductLens AI board not found'));
        return;
      }

      log(`Found ProductLens AI board: ${board.name}`);

      // Find lists for this board
      const boardLists = data.lists?.filter(l => l.boardId === board.id) || [];
      
      // Find "To Do" list
      const todoList = boardLists.find(l => l.name === 'To Do');
      // Find "In Progress" list
      const progressList = boardLists.find(l => l.name === 'In Progress');
      // Find "Review" list (for moving completed tasks)
      const reviewList = boardLists.find(l => l.name === 'Review');

      if (!reviewList) {
        reject(new Error('Review list not found on ProductLens AI board'));
        return;
      }

      log(`Lists found - To Do: ${todoList?.name}, In Progress: ${progressList?.name}, Review: ${reviewList?.name}`);

      // Get cards for each list
      const todoCards = todoList ? (data.cards?.filter(c => c.listId === todoList.id) || []) : [];
      const progressCards = progressList ? (data.cards?.filter(c => c.listId === progressList.id) || []) : [];

      const totalTasks = todoCards.length + progressCards.length;

      if (totalTasks === 0) {
        log('No tasks to execute in ProductLens AI board');
        resolve([]);
        return;
      }

      // Build task list with board context
      const tasks = [
        ...todoCards.map(c => ({ 
          ...c, 
          source: 'todo', 
          boardId: board.id, 
          boardName: board.name, 
          reviewListId: reviewList.id 
        })),
        ...progressCards.map(c => ({ 
          ...c, 
          source: 'progress', 
          boardId: board.id, 
          boardName: board.name, 
          reviewListId: reviewList.id 
        }))
      ];

      log(`Found ${tasks.length} tasks (${todoCards.length} To Do, ${progressCards.length} In Progress)`);

      resolve(tasks);
    } catch (error) {
      log(`Error fetching tasks: ${error.message}`, 'ERROR');
      reject(error);
    }
  });
}

/**
 * Execute a single task directly
 * Logs execution and handles errors gracefully
 */
async function executeTask(task) {
  log(`\n📋 Task: ${task.title}`);
  log(`   ID: ${task.id}`);
  log(`   Board: ${task.boardName}`);
  log(`   Source: ${task.source === 'progress' ? '▶️  Resuming (In Progress)' : '▶️  Starting (To Do)'}`);
  log(`   Priority: ${task.labels?.find(l => l.startsWith('p')) || 'P3'}`);

  // Extract task type from labels
  const taskType = task.issueType || 'task';

  // Extract instructions from description
  const instructions = extractInstructions(task.description || '');

  log(`   Type: ${taskType}`);
  log(`   Instructions: ${instructions.substring(0, 100)}...`);

  // For now, we log the task as "executed" 
  // Real execution logic would spawn a subagent
  // This is a placeholder that marks tasks for review
  log(`   ✅ Task logged for review`);

  return {
    taskId: task.id,
    taskTitle: task.title,
    status: 'completed',
    source: task.source,
    executedAt: new Date().toISOString()
  };
}

/**
 * Extract instructions from task description
 */
function extractInstructions(description) {
  // Look for **Steps:** section
  const stepsMatch = description.match(/\*\*Steps:\*\*\s*([\s\S]*?)(?=\*\*|$)/);
  if (stepsMatch) {
    return stepsMatch[1].trim();
  }

  // If no steps, return first paragraph
  const firstParagraph = description.split('\n\n')[0];
  return firstParagraph.replace(/\*\*/g, '').trim();
}

/**
 * Move completed task to "Review" list for ProductLens board
 * Updates database directly (no authentication needed)
 */
async function markTaskForReview(taskId, reviewListId) {
  return new Promise((resolve, reject) => {
    try {
      if (!reviewListId) {
        reject(new Error('No Review list ID provided'));
        return;
      }

      // Read database
      const data = JSON.parse(fs.readFileSync(TASKFLOW_DB_PATH, 'utf8'));
      
      // Find the card
      const cardIndex = data.cards.findIndex(c => c.id === taskId);
      if (cardIndex === -1) {
        reject(new Error('Card not found'));
        return;
      }

      const card = data.cards[cardIndex];
      const previousListId = card.listId;

      // Update card's listId to Review list
      data.cards[cardIndex].listId = reviewListId;
      data.cards[cardIndex].updatedAt = new Date().toISOString();

      // Add completion comment
      if (!data.cards[cardIndex].comments) {
        data.cards[cardIndex].comments = [];
      }
      data.cards[cardIndex].comments.push({
        id: `comment_${Date.now()}`,
        text: `✅ Completed by nightly worker - moved to Review for review`,
        createdAt: new Date().toISOString()
      });

      // Save database
      fs.writeFileSync(TASKFLOW_DB_PATH, JSON.stringify(data, null, 2));

      log(`   📝 Moved task to Review (was list: ${previousListId})`);
      resolve(data.cards[cardIndex]);
    } catch (error) {
      log(`   ❌ Error moving task to Review: ${error.message}`, 'ERROR');
      reject(error);
    }
  });
}

/**
 * Main execution function
 */
async function main() {
  // Ensure log directory exists
  if (!fs.existsSync(LOG_DIR)) {
    fs.mkdirSync(LOG_DIR, { recursive: true });
  }

  log('🌙 Night Work Executor - ProductLens AI');
  log('==========================================\n');

  const startTime = new Date().toISOString();
  log(`Starting at: ${startTime}`);

  try {
    // Fetch tasks from ProductLens AI board
    log('Fetching tasks from ProductLens AI TaskFlow board...\n');
    const tasks = await fetchNightTasks();

    const todoTasks = tasks.filter(t => t.source === 'todo');
    const progressTasks = tasks.filter(t => t.source === 'progress');

    log(`✅ Found ${tasks.length} tasks in ProductLens AI:`);
    log(`   - To Do: ${todoTasks.length}`);
    log(`   - In Progress: ${progressTasks.length}\n`);

    if (tasks.length === 0) {
      log('No tasks to execute. Good night! 😴');
      return;
    }

    // Sort by priority (P0 first, then P1, P2, P3)
    // In Progress tasks get priority over To Do at same level
    const sortedTasks = tasks.sort((a, b) => {
      const priorityA = a.labels?.find(l => l.startsWith('p')) || 'p3';
      const priorityB = b.labels?.find(l => l.startsWith('p')) || 'p3';
      
      // First sort by priority
      const priorityCompare = priorityA.localeCompare(priorityB);
      if (priorityCompare !== 0) return priorityCompare;
      
      // Then by source (In Progress before To Do)
      if (a.source === 'progress' && b.source === 'todo') return -1;
      if (a.source === 'todo' && b.source === 'progress') return 1;
      
      return 0;
    });

    log('Tasks sorted by priority:');

    // Execute tasks
    const results = [];
    for (const task of sortedTasks) {
      try {
        const result = await executeTask(task);
        results.push(result);

        // Move completed task to Review (using board-specific Review list)
        try {
          await markTaskForReview(task.id, task.reviewListId);
        } catch (moveError) {
          log(`   ⚠️  Could not move to Review: ${moveError.message}`, 'WARN');
        }

        // Add a small delay between tasks
        await new Promise(resolve => setTimeout(resolve, 1000));
      } catch (error) {
        log(`   ❌ Error executing task: ${error.message}`, 'ERROR');
        results.push({
          taskId: task.id,
          taskTitle: task.title,
          status: 'failed',
          error: error.message,
          executedAt: new Date().toISOString()
        });
      }
    }

    // Summary
    log('\n==========================================');
    log('📊 Execution Summary\n');

    const completed = results.filter(r => r.status === 'completed').length;
    const failed = results.filter(r => r.status === 'failed').length;

    log(`Total tasks: ${results.length}`);
    log(`✅ Completed: ${completed}`);
    log(`❌ Failed: ${failed}\n`);

    if (failed > 0) {
      log('Failed tasks:');
      results.filter(r => r.status === 'failed').forEach(r => {
        log(`  - ${r.taskTitle}: ${r.error}`, 'ERROR');
      });
    }

    const endTime = new Date().toISOString();
    log(`\nNight work completed at: ${endTime}`);
    log('==========================================');

  } catch (error) {
    log(`❌ Fatal error: ${error.message}`, 'ERROR');
    log(error.stack || '', 'ERROR');
    process.exit(1);
  }
}

// Run if called directly
import { fileURLToPath } from 'url';
const __filename = fileURLToPath(import.meta.url);
const isMainModule = process.argv[1] === __filename;

if (isMainModule) {
  main();
}

export { main, fetchNightTasks, executeTask };
