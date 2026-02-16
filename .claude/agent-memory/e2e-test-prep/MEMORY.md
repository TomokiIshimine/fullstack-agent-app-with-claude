# E2E Test Prep Agent Memory

## curl JSON escaping issue

When testing login API via curl in this environment, the shell (zsh) corrupts
JSON containing special characters (e.g., `!` in `Test123!`), producing
"Failed to decode JSON object: Invalid \escape" errors. Even `--data-raw` and
`printf` piping do not resolve the issue.

**Workaround**: Use Python `urllib.request` for login verification instead of curl:

```bash
python3 -c "
import json, urllib.request
data = json.dumps({'email': 'admin@example.com', 'password': 'Test123!'}).encode('utf-8')
req = urllib.request.Request('http://localhost:5001/api/auth/login', data=data, headers={'Content-Type': 'application/json'}, method='POST')
try:
    with urllib.request.urlopen(req) as resp:
        print(f'Status: {resp.status}')
        print(resp.read().decode('utf-8'))
except urllib.error.HTTPError as e:
    print(f'Status: {e.code}')
    print(e.read().decode('utf-8'))
"
```

## create_user.py CLI limitations

The `make db-create-user EMAIL=... PASSWORD=...` command does NOT support the
`role` parameter. The underlying script `backend/scripts/create_user.py` has
a `role` argument in the `create_user()` function, but `__main__` only reads
email and password from `sys.argv`.

**Workaround for admin creation**: Call the function directly:
```bash
poetry -C backend run python -c "
import sys; sys.path.insert(0, 'backend')
from scripts.create_user import create_user
create_user('admin@example.com', 'Test123!', role='admin', name='Administrator')
"
```

## Test accounts

| Email | Password | Role | Notes |
|-------|----------|------|-------|
| admin@example.com | Test123! | admin | id=1, name=Administrator |
| testuser@example.com | Test123! | user | id=5, name=null |

## Typical Phase 0 timings

- `make health`: ~2-3 seconds
- Login API calls (Python): ~0.5 seconds each
- Playwright navigate + snapshot: ~2-3 seconds
- Total Phase 0: ~5-8 seconds when all services are running
