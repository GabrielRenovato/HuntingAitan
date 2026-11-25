"""Diagnostico limitado: um duplo clique pela janela e observacao da interacao manual."""
from pathlib import Path
import os,sys,json,time,struct,ctypes,math

raiz=Path(__file__).resolve().parents[1];sys.path.insert(0,str(raiz))
from ctypes import wintypes as w
from huntingaitan.leitura.escolha_cliente import abrir_leitor
from huntingaitan.entrada.entrada_janela import EntradaJanela
from huntingaitan.visao.captura_janela import CapturaJanela
from huntingaitan.rotas.interface_jardim import InterfaceJardim
from huntingaitan.rotas.entrada_jardim import PORTAL


def estado(d):
    cena=d.cena_validada();p=d.snapshot()['player']
    ui=d.u32(d.base+0x2f4cd90);grafico=d.u32(d.base+0x2e266ac)
    cursor=struct.unpack('<2h',d.read(ui+0x3c,4))
    raio=struct.unpack('<6f',d.read(grafico+0x5c0,24))
    if not all(math.isfinite(v) for v in raio):raise RuntimeError('Raio invalido')
    entidades={}
    for nome,offset in [('selecionado',0x90),('sob_cursor',0x108)]:
        ptr=d.u32(cena+offset);e=dict(ref=hex(ptr))
        if ptr:
            try:
                e.update(id=d.u32(ptr+4),nome=d.read(ptr+0x19ac,128).split(b'\0')[0].decode('cp1252',errors='replace'))
            except RuntimeError:e['campos_indisponiveis']=True
        entidades[nome]=e
    return dict(posicao=p['position'],hp=p['hp']/p['hp_max'],cursor=cursor,raio=raio,**entidades)


def main():
    import cv2,keyboard
    perfil=json.loads((Path(os.environ['APPDATA'])/'aika-caca-automatica/profile.json').read_text(encoding='utf-8'))
    pasta=raiz/'build'/('comparacao_altar_'+time.strftime('%Y%m%d_%H%M%S'));pasta.mkdir()
    (raiz/'build/ultima_comparacao_altar.txt').write_text(str(pasta),encoding='utf-8')
    resultado=dict(fase='iniciar',cliques_automaticos=0);d=None
    u=ctypes.WinDLL('user32');u.GetForegroundWindow.restype=w.HWND
    u.GetCursorPos.argtypes=[ctypes.POINTER(w.POINT)]
    def salvar():(pasta/'resultado.json').write_text(json.dumps(resultado,ensure_ascii=False,indent=2),encoding='utf-8')
    try:
        d=abrir_leitor(perfil['client_pid'])
        if d.hwnd!=perfil['client_hwnd'] or d.snapshot()['player']['name']!='Domination':raise RuntimeError('Cliente diferente da templaria selecionada')
        if d.caca_original_ativa():raise RuntimeError('Pare a caca original antes do diagnostico')
        e=EntradaJanela(d.hwnd,d.pid);inicio=time.monotonic();tentou=False;foto_em=0
        with CapturaJanela(d.hwnd,d.pid) as cap,(pasta/'amostras.jsonl').open('w',encoding='utf-8') as log:
            while time.monotonic()-inicio<80:
                t=time.monotonic()-inicio
                if keyboard.is_pressed('f12') or (pasta/'PARAR').exists():break
                s=estado(d);s.update(t=round(t,3),foco=int(u.GetForegroundWindow() or 0),ao_fundo=u.GetForegroundWindow()!=d.hwnd)
                cursor=w.POINT();u.GetCursorPos(ctypes.byref(cursor));s['cursor_desktop']=[cursor.x,cursor.y]
                if s['hp']<.9:raise RuntimeError('HP abaixo de 90%; diagnostico interrompido')
                if d.caca_original_ativa():raise RuntimeError('Caca original iniciada; diagnostico interrompido')
                log.write(json.dumps(s,ensure_ascii=False)+'\n');log.flush()
                resultado.update(fase='comparacao_manual' if t>=18 else 'clique_ao_fundo',ultima=s)
                if t>=5 and not tentou:
                    tentou=True
                    if not s['ao_fundo']:raise RuntimeError('Aika em foco no teste ao fundo; nenhum clique enviado')
                    if math.dist(s['posicao'],PORTAL)>4:raise RuntimeError('Personagem fora do alcance do altar')
                    ui=InterfaceJardim();imagem=cap.capturar();acao=ui.entrada(imagem)
                    cv2.imwrite(str(pasta/'antes.png'),imagem)
                    resultado['acao']=acao
                    if acao.get('acao')!='abrir_portal' or 'ponto' not in acao:raise RuntimeError('Altar nao reconhecido; nenhum clique enviado')
                    atual=ui.reconfirmar(cap.capturar(),acao)
                    if atual.get('acao')!='abrir_portal' or 'ponto' not in atual:raise RuntimeError('Altar nao reconfirmado')
                    x,y=atual['ponto'];cap.capturar()
                    if not e.disponivel() or not e.mover_sem_cursor(cap.area['left']+x,cap.area['top']+y):raise RuntimeError('Entrada da janela indisponivel')
                    time.sleep(.08)
                    for i in range(2):
                        if not e.disponivel():raise RuntimeError('Entrada interrompida')
                        e.mouseDown(duplo=bool(i))
                        try:time.sleep(.065)
                        finally:e.mouseUp()
                        time.sleep(.10)
                    resultado['cliques_automaticos']=1
                if t>=foto_em:
                    cv2.imwrite(str(pasta/f'quadro_{int(t):02d}.png'),cap.capturar());foto_em=t+4
                salvar();time.sleep(.2)
    except Exception as exc:resultado['erro']=str(exc)
    finally:
        if d:d.close()
        resultado['fase']='encerrado';salvar()


if __name__=='__main__':main()
