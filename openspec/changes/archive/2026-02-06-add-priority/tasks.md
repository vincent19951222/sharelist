# Tasks: Add Task Priority Feature

## Phase 1: Database & Backend
- [x] Create database migration to add `priority` column to `todoitem` table
- [x] Update `TodoItem` model in `backend/models.py` to include priority field
- [x] Add priority validation function in backend (VALID_PRIORITIES constant)
- [x] Update `item_add` WebSocket handler to accept and validate priority
- [x] Update `item_edit` WebSocket handler to accept and validate priority
- [x] Add error handling for invalid priority values

## Phase 2: Frontend Components
- [x] Create `PriorityBadge.tsx` component with color styling
- [x] Create `PrioritySelector.tsx` dropdown component
- [x] Add priority field to TodoItem TypeScript interface
- [x] Update TodoItem component to display PriorityBadge
- [x] Update AddItem form to include PrioritySelector
- [x] Update EditItem modal to include PrioritySelector

## Phase 3: Filtering Feature
- [x] Create `FilterBar.tsx` component
- [x] Add filter state to room context
- [x] Implement filter logic in todo list rendering
- [x] Test filter interactions

## Phase 4: Documentation & Testing
- [x] Update `EVENT_PROTOCOL.md` with priority field documentation
- [x] Write unit tests for priority validation (backend)
- [x] Write integration tests for WebSocket events
- [x] Manual E2E testing in development environment
- [x] Update README.md with new feature documentation

## Phase 5: Deployment
- [x] Test migration on staging database
- [x] Deploy backend changes
- [x] Run database migration
- [x] Deploy frontend changes
- [x] Smoke test in production
- [x] Monitor for errors
