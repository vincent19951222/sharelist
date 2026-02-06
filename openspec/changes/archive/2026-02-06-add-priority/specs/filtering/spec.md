# Spec: Priority Filtering

## Overview
Users can filter the task list to show only tasks of specific priority levels.

## UI Component
Add a filter bar above the task list:
```
[All] [High] [Medium] [Low]
```

## Interaction
- Click filter button → Show only tasks with that priority
- "All" shows all tasks (default)
- Only one filter active at a time
- Active filter highlighted

## Behavior
- Filtering is local (doesn't affect other users)
- Filter state persists per session
- New tasks appear even if filter is active (unless they don't match)

## Keyboard Shortcuts (Optional)
- `Ctrl+1` → All
- `Ctrl+2` → High
- `Ctrl+3` → Medium
- `Ctrl+4` → Low
