"""Publica o mesmo feed tambem no canal beta, inclusive ao promover uma estavel."""
from pathlib import Path
import base64,hashlib,json,re,shutil

root=Path(__file__).resolve().parents[1]
version=json.loads((root/'aika_hunt_app/package.json').read_text(encoding='utf-8'))['version']
release=root/'release';feed=release/'latest.yml';text=feed.read_text(encoding='utf-8')
if f'version: {version}' not in text:raise SystemExit('Feed aponta para versao incorreta')
installer=release/f'HuntingAitan-Setup-{version}-x64.exe'
digest=base64.b64encode(hashlib.sha512(installer.read_bytes()).digest()).decode('ascii')
if not re.search(r'sha512: '+re.escape(digest)+r'(?:\s|$)',text):raise SystemExit('Hash do instalador difere do feed')
shutil.copyfile(feed,release/'beta.yml')
print('Feeds latest e beta conferidos; SHA-512 do instalador validado.')
