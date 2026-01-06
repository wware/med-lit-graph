# Testing Issues and Future Work

## Duplicate Table Registration Error

### Problem
When running the full test suite (`pytest tests/`), two PostgreSQL integration tests fail with:
```
sqlalchemy.exc.InvalidRequestError: Table 'entities' is already defined for this MetaData instance.
```

### Affected Tests
- `test_vector_search`
- `test_path_query`

### Current Status
- ✅ All tests pass when run individually
- ✅ All tests pass when running only `test_postgresql_integration.py`
- ✅ All non-PostgreSQL tests pass when run together
- ❌ 2 tests fail when running the entire test suite together

### Root Cause
The issue occurs at the Python/SQLModel metadata level, not the database level:

1. SQLModel uses a singleton `metadata` registry (`SQLModel.metadata`)
2. When model classes (`Entity`, `Relationship`) are defined, they register themselves with this metadata
3. During test collection/execution, the models get imported multiple times:
   - First import: `conftest.py` imports models in the `postgres_container` fixture
   - Second import: `setup_database.py` also imports models (or accesses them)
4. The second import/access triggers a duplicate registration error

### Why Current Workarounds Don't Work
- **Dropping/recreating database tables**: Doesn't help - the issue is in Python memory, not the database
- **Checking if tables exist in metadata**: Race condition - by the time we check, the class definition has already executed
- **Using `extend_existing=True`**: Only works for `create_all()`, not for the class definition itself

### Potential Solutions (Future Work)

1. **Lazy Model Registration**: Modify model classes to check if already registered before registering
2. **Single Import Point**: Ensure models are only imported once, in one place (e.g., only in `conftest.py`)
3. **Metadata Isolation**: Use separate metadata instances for different test contexts (complex, may break other things)
4. **Test Isolation**: Run PostgreSQL integration tests in a separate pytest session or process
5. **Refactor setup_database**: Make it not import models at all, require them to be pre-imported

### Current Workaround
Run tests in smaller groups:
```bash
# All non-PostgreSQL tests
pytest tests/ -k "not postgresql_integration"

# PostgreSQL tests separately
pytest tests/test_postgresql_integration.py
```

### Related Files
- `tests/conftest.py` - Imports models in `postgres_container` fixture
- `schema/setup_database.py` - Also imports/accesses models
- `schema/entity_sqlmodel.py` - Defines Entity class that registers with metadata
- `schema/relationship_sqlmodel.py` - Defines Relationship class that registers with metadata
