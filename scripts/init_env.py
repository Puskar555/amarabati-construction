"""Create secret local .env; never ship a universal default account/password."""
from pathlib import Path
import base64
import os
import secrets

root=Path(__file__).resolve().parents[1]
path=root/'.env'
if path.exists():
    raise SystemExit('Existing .env kept intact; refusing to overwrite local credentials.')
key=base64.urlsafe_b64encode(os.urandom(32)).decode()
path.write_text(f'''# Local development secrets - NEVER commit or share
PG_OWNER_PASSWORD={secrets.token_urlsafe(32)}
PG_APP_PASSWORD={secrets.token_urlsafe(32)}
APP_SIGNING_KEY={secrets.token_hex(48)}
TOTP_ENCRYPTION_KEY={key}
''')
try:path.chmod(0o600)
except OSError:pass
print('Generated local .env with random credentials. Keep this private.')
