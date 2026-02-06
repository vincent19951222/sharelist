# Proposal: Add Task Priority Feature

## Why
Users need to distinguish between urgent and less important tasks. Currently, all tasks have equal weight, making it difficult to prioritize work in collaborative settings.

## What Changes
Add a `priority` field to TodoItem model with three levels: **high**, **medium**, **low**.

## Capabilities
- [Priority Levels] Users can assign priority levels (high/medium/low) to tasks
- [Visual Indicators] UI displays priority with color-coded badges
- [Filtering] Users can filter tasks by priority level
- [Default Value] New tasks default to "medium" priority

## Impact
- **Database Schema**: Add `priority` column to `todoitem` table
- **API**: Update WebSocket event protocol to include priority in payloads
- **Frontend**: Add priority selector and visual indicators
- **Backward Compatibility**: Existing items will default to "medium" priority
