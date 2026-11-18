from pathlib import Path
import json,re,sys
root=Path(__file__).resolve().parents[1]
v=json.loads((root/'aika_hunt_app/package.json').read_text(encoding='utf-8'))['version']
if not re.fullmatch(r'\d+\.\d+\.\d+(?:-(?:alpha|beta|rc)\.\d+)?',v):raise SystemExit('Versao invalida: '+v)
if len(sys.argv)>1 and sys.argv[1]!='v'+v:raise SystemExit('Tag e package.json precisam ter a mesma versao')
print('Versao validada:',v)

for nome in ['package.json','package-lock.json','aika_hunt_app/package-lock.json']:
    dados=json.loads((root/nome).read_text(encoding='utf-8'))
    if dados.get('version')!=v:raise SystemExit('Versao divergente em '+nome)
    if 'packages' in dados and dados['packages'][''].get('version')!=v:raise SystemExit('Versao divergente no pacote raiz de '+nome)
