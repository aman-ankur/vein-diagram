# Database Migration Best Practices & Troubleshooting

## Overview

This document outlines best practices for database schema management in the Vein Diagram project to prevent production deployment failures due to schema mismatches.

## Incident Summary (July 26, 2025)

### **Problem**
Production deployment failed with error:
```
sqlalchemy.exc.ProgrammingError: (psycopg2.errors.UndefinedColumn) 
column pdfs_1.processing_started_at does not exist
```

### **Root Cause**
- The `processing_started_at` column existed in SQLAlchemy models but was missing from the Supabase database
- A standalone migration script existed (`migrations/add_processing_started_at.py`) but was never integrated into the Alembic migration system
- Both local and production environments connected to the same Supabase database, but the column was never actually added

### **Resolution**
- Added missing column directly via Supabase: `ALTER TABLE pdfs ADD COLUMN processing_started_at TIMESTAMP;`
- Production immediately started working

## Best Practices

### 1. **Always Use Proper Alembic Migrations**

#### ✅ DO THIS
```bash
# Create a proper Alembic migration
cd backend
alembic revision --autogenerate -m "add processing_started_at to pdfs table"
alembic upgrade head
```

#### ❌ DON'T DO THIS  
- Creating standalone migration scripts outside of Alembic
- Manually adding columns without proper version control
- Assuming local changes are reflected in production

### 2. **Migration Workflow**

#### **For New Schema Changes:**
1. **Modify SQLAlchemy Models** first
2. **Generate Alembic Migration**:
   ```bash
   alembic revision --autogenerate -m "descriptive message"
   ```
3. **Review Generated Migration** - ensure it's correct
4. **Test Migration Locally**:
   ```bash
   alembic upgrade head
   ```
5. **Commit Migration Files** to git
6. **Deploy** - migrations run automatically via `start.sh`

#### **For Production Hotfixes:**
1. **Apply Database Fix** (if urgent)
2. **Create Corresponding Alembic Migration** immediately after
3. **Mark Migration as Applied**:
   ```bash
   alembic stamp head
   ```

### 3. **Environment Synchronization**

#### **Local Development:**
- Always use the same database type as production (PostgreSQL via Supabase)
- Run `alembic upgrade head` after pulling new code
- Verify schema matches production before deploying

#### **Production Deployment:**
- The `start.sh` script automatically runs `alembic upgrade head`
- Monitor deployment logs for migration failures
- Have rollback plan ready

### 4. **Database Schema Validation**

#### **Pre-Deployment Checks:**
```bash
# Check current migration status
alembic current

# Check if migrations are pending
alembic show head

# Validate models match database
python -c "from app.db.database import engine; from sqlalchemy import inspect; print(inspect(engine).get_table_names())"
```

#### **Production Health Checks:**
- Implement `/health` endpoint that validates database connectivity
- Add schema validation checks in health endpoint
- Monitor for SQLAlchemy errors in production logs

### 5. **Schema Change Checklist**

Before any deployment involving database changes:

- [ ] SQLAlchemy models updated
- [ ] Alembic migration created and reviewed
- [ ] Migration tested locally
- [ ] Migration files committed to git
- [ ] Production backup taken (if destructive changes)
- [ ] Deployment monitored for migration success
- [ ] API endpoints tested post-deployment

## Common Pitfalls & Solutions

### **Problem: "Column does not exist" errors**
**Cause**: Model-database schema mismatch
**Solution**: 
1. Check `alembic current` vs `alembic show head`
2. Run missing migrations or create new ones
3. Use `alembic stamp` if manual fixes were applied

### **Problem: Migration conflicts**
**Cause**: Multiple developers creating overlapping migrations
**Solution**:
1. Always pull latest code before creating migrations
2. Use descriptive migration messages
3. Resolve conflicts by merging migration files

### **Problem: Production data loss**
**Cause**: Destructive migrations without backups
**Solution**:
1. Always backup before destructive changes
2. Test migrations on staging data first
3. Use reversible migrations when possible

## Tools & Commands

### **Essential Alembic Commands:**
```bash
# Check current migration version
alembic current

# Show latest migration
alembic heads

# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Mark migration as applied (without running)
alembic stamp head

# Show migration history
alembic history
```

### **Database Inspection:**
```bash
# Connect to Supabase and check schema
psql $DATABASE_URL -c "\d pdfs"

# Check specific column exists
psql $DATABASE_URL -c "SELECT column_name FROM information_schema.columns WHERE table_name='pdfs' AND column_name='processing_started_at';"
```

## Monitoring & Alerts

### **What to Monitor:**
- Migration success/failure in deployment logs
- SQLAlchemy errors in application logs
- Database connectivity in health checks
- Schema drift between environments

### **Alert Conditions:**
- Migration failures during deployment
- "Column does not exist" errors
- "Table does not exist" errors
- Alembic version mismatches

## Environment-Specific Considerations

### **Local Development:**
- Use same PostgreSQL version as production
- Run migrations after every git pull
- Keep local schema synchronized

### **Production (Render + Supabase):**
- Migrations run automatically via `start.sh`
- Monitor Render deployment logs
- Use Supabase dashboard for emergency schema fixes
- Enable connection pooling for performance

## Emergency Procedures

### **If Production is Down Due to Schema Issues:**

1. **Immediate Fix** (if column missing):
   ```sql
   ALTER TABLE table_name ADD COLUMN column_name TYPE;
   ```

2. **Create Corresponding Migration**:
   ```bash
   alembic revision -m "add missing column (hotfix)"
   # Edit migration file to match the manual change
   alembic stamp head
   ```

3. **Verify Fix**:
   - Test API endpoints
   - Check application logs
   - Monitor error rates

### **If Migration Fails During Deployment:**

1. **Check Render logs** for specific error
2. **Connect to Supabase** to inspect database state
3. **Fix manually** if needed, then create corresponding migration
4. **Redeploy** after verification

## Related Files

- `backend/alembic/` - Migration files directory
- `backend/start.sh` - Deployment script that runs migrations
- `backend/app/models/` - SQLAlchemy model definitions
- `backend/migrations/` - Standalone scripts (avoid using)

## Best Practices Summary

1. **Always use Alembic** for schema changes
2. **Test migrations locally** before deployment  
3. **Keep environments synchronized**
4. **Monitor deployments** for migration issues
5. **Have rollback plans** ready
6. **Validate schema** matches models
7. **Document all changes** in migration messages

Following these practices will prevent database schema mismatches and ensure smooth deployments.