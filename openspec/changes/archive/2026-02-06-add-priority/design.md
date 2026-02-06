# Design: Task Priority Feature

## Architecture Overview
Priority feature spans three layers:
```
Frontend (Next.js)  ←→  WebSocket (FastAPI)  ←→  Database (PostgreSQL)
```

## Database Migration

### Schema Change
```sql
ALTER TABLE todoitem
ADD COLUMN priority VARCHAR(10) DEFAULT 'medium';

ALTER TABLE todoitem
ADD CONSTRAINT check_priority
CHECK (priority IN ('high', 'medium', 'low'));

-- Set existing items to medium
UPDATE todoitem
SET priority = 'medium'
WHERE priority IS NULL;
```

### Migration Strategy
1. Add column as nullable first
2. Backfill existing rows with "medium"
3. Add NOT NULL constraint
4. Add CHECK constraint for valid values

## Backend Changes

### Models Update
```python
# backend/models.py
class TodoItem(SQLModel, table=True):
    # ... existing fields ...
    priority: str = Field(default="medium")  # new field
```

### WebSocket Event Handlers
Update `item_add` and `item_edit` handlers to validate priority:
```python
VALID_PRIORITIES = {"high", "medium", "low"}

def validate_priority(priority: str | None) -> str:
    if priority is None:
        return "medium"
    if priority not in VALID_PRIORITIES:
        raise ValueError(f"Invalid priority: {priority}")
    return priority
```

## Frontend Changes

### Components
1. **PriorityBadge.tsx** - Display priority badge
2. **PrioritySelector.tsx** - Dropdown to select priority
3. **FilterBar.tsx** - Filter by priority

### State Management
```typescript
type Priority = "high" | "medium" | "low"

interface TodoItem {
  // ... existing fields ...
  priority: Priority
}

interface FilterState {
  priority: "all" | Priority
}
```

### Event Protocol Update
Update `EVENT_PROTOCOL.md` with new field.

## Security & Validation
- Server-side validation: Reject invalid priorities
- Client-side validation: Prevent invalid values before sending
- SQL injection prevention: Use parameterized queries

## Performance Considerations
- Add index on `priority` column if filtering becomes slow
- Minimal overhead (single VARCHAR column)

## Testing Strategy
1. Unit tests for validation logic
2. Integration tests for WebSocket events
3. E2E tests for UI interactions
4. Migration test on sample data

## Rollback Plan
If issues arise:
1. Remove UI components
2. Revert WebSocket handlers
3. Keep database column (harmless if unused)
4. Or: Drop column via migration
