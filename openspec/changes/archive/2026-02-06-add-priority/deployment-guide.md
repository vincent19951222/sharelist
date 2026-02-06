# Deployment Guide: Priority Feature

## Pre-deployment Checklist

### 1. Testing
- [ ] All unit tests pass
- [ ] Integration tests pass
- [ ] E2E tests pass
- [ ] Manual testing completed
- [ ] Accessibility audit passed

### 2. Code Review
- [ ] Code reviewed by team
- [ ] Security review completed
- [ ] Performance impact assessed
- [ ] Documentation updated

### 3. Staging Environment
- [ ] Feature branch merged to staging
- [ ] Migration tested on staging database
- [ ] Smoke tests pass on staging
- [ ] Performance acceptable

## Deployment Steps

### Phase 1: Database Migration
⚠️ **CRITICAL**: Backup database before migration!

```bash
# 1. Backup production database
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d_%H%M%S).sql

# 2. Run migration
cd backend
python migrations/add_priority_column.py

# 3. Verify migration
psql $DATABASE_URL
\d todoitem  -- Should show priority column
SELECT COUNT(*) FROM todoitem WHERE priority IS NULL;  -- Should be 0
```

### Phase 2: Backend Deployment
```bash
# Deploy backend changes
docker-compose build backend
docker-compose up -d backend

# Verify health
curl http://localhost:8000/sys/stats
```

### Phase 3: Frontend Deployment
```bash
# Deploy frontend changes
docker-compose build frontend
docker-compose up -d frontend

# Verify frontend
curl http://localhost:3000
```

## Post-deployment Verification

### Health Checks
- [ ] Backend responds to health checks
- [ ] Frontend loads without errors
- [ ] WebSocket connections work
- [ ] Database queries execute successfully

### Functional Tests
- [ ] Create new room
- [ ] Add items with different priorities
- [ ] Verify priority badges display
- [ ] Test filtering functionality
- [ ] Edit item priorities
- [ ] Verify persistence across page refresh

### Monitoring
- [ ] Check error logs for priority-related errors
- [ ] Monitor database performance
- [ ] Track WebSocket message latency
- [ ] Monitor user feedback

## Rollback Plan

If issues occur:

### Option 1: UI Rollback (Fastest)
```bash
# Revert frontend code only
git revert <commit-hash>
docker-compose build frontend
docker-compose up -d frontend
```

### Option 2: Full Rollback
```bash
# Revert all changes
git revert <backend-commit>
git revert <frontend-commit>

# Rollback database migration
psql $DATABASE_URL
ALTER TABLE todoitem DROP COLUMN priority;

# Rebuild services
docker-compose down
docker-compose up -d --build
```

## Success Metrics

- No increase in error rate
- No degradation in WebSocket performance
- User adoption of priority feature > 20% within 1 week
- Zero data loss incidents
