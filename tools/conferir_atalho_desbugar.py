"""Confere somente leitura da barra e dos VKs do apostrofo no cliente escolhido."""
import ctypes,json,os,sys
from pathlib import Path
from ctypes import wintypes as w
raiz=Path(__file__).resolve().parents[1];sys.path.insert(0,str(raiz))
from huntingaitan.leitura.janela_cliente import enumerar_clientes
from huntingaitan.leitura.dados_internos import DadosInternos
from huntingaitan.leitura.skills_cliente import descrever_barra
from huntingaitan.leitura.recargas_barra import atalhos_slots
r=[]
for nome in ('aika-caca-automatica','aika-caca-automatica-segundo'):
    d=None;t=dict(perfil=nome);r.append(t)
    try:
        p=json.loads((Path(os.environ['APPDATA'])/nome/'profile.json').read_text(encoding='utf-8'))
        j=next(j for j in enumerar_clientes() if j['pid']==p['client_pid'] and j['hwnd']==p['client_hwnd'])
        d=DadosInternos(janela=j);gestor=d.u32(d.base+d.cfg('bar_manager_rva'));raw=d.read(gestor+0x430,468)
        mapa=atalhos_slots(raw);barra=descrever_barra(d)
        for slot in barra:slot['tecla']=mapa.get(slot['slot'])
        u=ctypes.WinDLL('user32');u.GetWindowThreadProcessId.argtypes=[w.HWND,ctypes.POINTER(w.DWORD)]
        u.GetKeyboardLayout.argtypes=[w.DWORD];u.GetKeyboardLayout.restype=w.HANDLE
        u.MapVirtualKeyExW.argtypes=[w.UINT,w.UINT,w.HANDLE];u.MapVirtualKeyExW.restype=w.UINT
        thread=u.GetWindowThreadProcessId(d.hwnd,None);layout=u.GetKeyboardLayout(thread)
        t.update(ok=True,nome=d.snapshot()['player']['name'],barra=barra,apostrofo=d.recargas_atalhos().get("'"),
            teclas=[dict(indice=i,vk=raw[i*4],mod=raw[i*4+1],char=u.MapVirtualKeyExW(raw[i*4],2,layout)&0xffff) for i in range(len(raw)//4) if raw[i*4] in (192,222)])
    except Exception as e:t.update(ok=False,erro=str(e))
    finally:
        if d:d.close()
(raiz/'build/atalho_desbugar.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
