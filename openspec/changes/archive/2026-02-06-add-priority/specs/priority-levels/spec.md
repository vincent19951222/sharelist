# Spec: Priority Levels

## Overview
Users can assign one of three priority levels to any task: high, medium, or low.

## Data Model
```python
class TodoItem(SQLModel, table=True):
    # ... existing fields ...
    priority: str = Field(default="medium")  # "high" | "medium" | "low"
```

## Validation Rules
- Only accepts: "high", "medium", "low"
- Case-sensitive (lowercase only)
- Defaults to "medium" for new tasks
- Existing tasks default to "medium" on migration

## API Changes
**Add Item Event:**
```json
{
  "type": "item_add",
  "payload": {
    "clientEventId": "unique-id",
    "text": "Urgent task",
    "priority": "high"  // optional, defaults to "medium"
  }
}
```

**Edit Item Event (update priority):**
```json
{
  "type": "item_edit",
  "payload": {
    "clientEventId": "unique-id",
    "itemId": "uuid",
    "priority": "low"  // new field
  }
}
```

## Edge Cases
- Invalid priority values → Return error, reject change
- Missing priority on add → Default to "medium"
- Null priority → Treat as "medium"

## Error Messages
- "Invalid priority. Use: high, medium, or low"
