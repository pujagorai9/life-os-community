"""Check tracked filenames and obvious owner-specific deployment remnants."""
from pathlib import Path
import re
import subprocess
ROOT = Path(__file__).resolve().parents[1]
tracked = subprocess.check_output(['git', 'ls-files'], cwd=ROOT, text=True).splitlines()
blocked = []
for name in tracked:
    path = Path(name)
    if (any(part in {'private', 'node_modules', '.venv', '.next', '.openai', '.wrangler', 'work'} for part in path.parts)
        or (path.name.startswith('.env') and path.name != '.env.example')
        or path.suffix in {'.db', '.sqlite', '.sqlite3', '.pem', '.key'}):
        blocked.append(name)
    try:
        content = (ROOT / name).read_text()
    except (UnicodeError, OSError):
        continue
    # Reject absolute macOS home paths and source-host deployment bindings.
    if re.search(r'/Users/[A-Za-z0-9._-]+/|appgprj_[a-zA-Z0-9]+', content):
        blocked.append(name)
if blocked:
    raise SystemExit('Publication check failed for: ' + ', '.join(sorted(set(blocked))))
print(f'Public tree check passed ({len(tracked)} tracked files).')
