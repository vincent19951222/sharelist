# Testing Checklist: Priority Feature

## Integration Tests (Manual)

### WebSocket Events
- [ ] Test `item_add` with valid priority (high, medium, low)
- [ ] Test `item_add` with missing priority (should default to medium)
- [ ] Test `item_add` with invalid priority (should return error)
- [ ] Test `item_edit` updating priority alone
- [ ] Test `item_edit` updating both text and priority
- [ ] Test `item_edit` with invalid priority (should return error)

### Database Operations
- [ ] Verify migration script runs successfully
- [ ] Check existing items get "medium" priority
- [ ] Verify CHECK constraint prevents invalid values
- [ ] Test rollback procedure

## E2E Tests (Manual)

### User Flow
1. [ ] Create a new room
2. [ ] Add items with different priorities
3. [ ] Verify badges display correctly
4. [ ] Test filtering by priority
5. [ ] Edit item priority
6. [ ] Verify all priorities persist after refresh

### Edge Cases
- [ ] Add item without selecting priority (defaults to medium)
- [ ] Try to add item with invalid priority (should show error)
- [ ] Filter when no items match
- [ ] Filter with mix of priorities
- [ ] Edit item text only (priority unchanged)
- [ ] Edit item priority only (text unchanged)

### Multi-user Testing
- [ ] User A adds high priority item
- [ ] User B sees correct priority badge
- [ ] User B edits priority to low
- [ ] User A sees updated priority

### Browser Compatibility
- [ ] Test in Chrome
- [ ] Test in Firefox
- [ ] Test in Safari
- [ ] Test in Edge
- [ ] Test on mobile browsers

## Performance Tests
- [ ] Add 200 items with various priorities
- [ ] Verify filter performance
- [ ] Check render time with badges
- [ ] Monitor memory usage

## Accessibility Tests
- [ ] Keyboard navigation for filters
- [ ] Screen reader announces priority
- [ ] Color contrast meets WCAG AA
- [ ] Touch targets are sufficient size (44px minimum)
