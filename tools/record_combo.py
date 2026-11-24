"""Calibracao manual: observa W/numeros no Aika; nunca envia ou bloqueia teclas."""
from pathlib import Path
import ctypes,json,queue,sys,threading,time
from ctypes import wintypes as w

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from huntingaitan.leitura.dados_internos import DadosInternos

def main():
    out=ROOT/'app_sessions'/('calibration_'+time.strftime('%Y%m%d_%H%M%S'))
    out.mkdir(parents=True)
    status=ROOT/'app_sessions/calibration_status.json'
    def state(value,**extra):
        temp=status.with_suffix('.tmp')
        temp.write_text(json.dumps(dict(state=value,directory=str(out),**extra)),encoding='utf-8')
        temp.replace(status)
    user=ctypes.WinDLL('user32',use_last_error=True)
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    user.GetForegroundWindow.restype=w.HWND
    user.GetWindowTextW.argtypes=[w.HWND,w.LPWSTR,ctypes.c_int]
    def foco():
        text=ctypes.create_unicode_buffer(256)
        user.GetWindowTextW(user.GetForegroundWindow(),text,256)
        return text.value=='AikaClient'
    class KBD(ctypes.Structure):
        _fields_=[('vk',w.DWORD),('scan',w.DWORD),('flags',w.DWORD),('tick',w.DWORD),('extra',ctypes.c_size_t)]
    callback_type=ctypes.WINFUNCTYPE(ctypes.c_ssize_t,ctypes.c_int,w.WPARAM,w.LPARAM)
    user.SetWindowsHookExW.argtypes=[ctypes.c_int,callback_type,w.HINSTANCE,w.DWORD]
    user.SetWindowsHookExW.restype=w.HHOOK
    user.CallNextHookEx.argtypes=[w.HHOOK,ctypes.c_int,w.WPARAM,w.LPARAM]
    user.CallNextHookEx.restype=ctypes.c_ssize_t
    user.UnhookWindowsHookEx.argtypes=[w.HHOOK]
    kernel.GetModuleHandleW.argtypes=[w.LPCWSTR];kernel.GetModuleHandleW.restype=w.HMODULE
    user.PeekMessageW.argtypes=[ctypes.POINTER(w.MSG),w.HWND,w.UINT,w.UINT,w.UINT]
    events=queue.SimpleQueue();active=threading.Event();done=threading.Event()
    started=[None];keys=set();counts={'manual':0,'injected_ignored':0}
    names={0x57:'w',**{i:str(i-0x30) for i in range(0x30,0x3a)},**{i:str(i-0x60) for i in range(0x60,0x6a)},0xa2:'ctrl',0xa3:'ctrl',0xa0:'shift',0xa1:'shift'}
    @callback_type
    def hook(code,message,pointer):
        try:
            if code>=0 and message in (0x100,0x101,0x104,0x105):
                k=ctypes.cast(pointer,ctypes.POINTER(KBD)).contents
                down=message in (0x100,0x104);now=time.perf_counter()
                if k.flags&0x10:
                    if active.is_set() and k.vk in names:counts['injected_ignored']+=1
                elif foco():
                    if k.vk==0x77 and down and not active.is_set():
                        started[0]=now;active.set();events.put(dict(event='start',t=0.))
                    elif k.vk==0x78 and down and active.is_set():done.set()
                    elif active.is_set() and k.vk in names:
                        repeat=down and k.vk in keys
                        if down:keys.add(k.vk)
                        else:keys.discard(k.vk)
                        counts['manual']+=1
                        events.put(dict(event='key',t=now-started[0],key=names[k.vk],type='down' if down else 'up',repeat=repeat,scan=k.scan))
        except Exception:done.set()
        return user.CallNextHookEx(None,code,message,pointer)
    reader=None;handle=None
    try:
        reader=DadosInternos()
        handle=user.SetWindowsHookExW(13,hook,kernel.GetModuleHandleW(None),0)
        if not handle:raise RuntimeError('Nao foi possivel iniciar observador de teclas: '+str(ctypes.get_last_error()))
        def observe():
            previous=None
            while not done.wait(.03):
                if not active.is_set():continue
                if not foco():
                    if previous is not False:events.put(dict(event='focus',t=time.perf_counter()-started[0],active=False))
                    previous=False;continue
                try:
                    snapshot=reader.snapshot();cc=reader.estados_controle();cd=reader.recargas_atalhos()
                    p=snapshot['player'];target=snapshot['target']
                    events.put(dict(event='game',t=time.perf_counter()-started[0],hp=p['hp'],hp_max=p['hp_max'],position=p['position'],target_id=target['id'] if target else None,target_hp=target['hp'] if target else None,animation=cc['animation'],casting=cc['casting'],stunned=cc['stunned'],cooldowns=cd))
                    previous=True
                except RuntimeError as e:events.put(dict(event='read_error',t=time.perf_counter()-started[0],message=str(e)))
        observer=threading.Thread(target=observe,daemon=True);observer.start()
        state('armed',start_key='F8',stop_key='F9')
        message=w.MSG();armed=time.perf_counter();notified=False
        with (out/'events.jsonl').open('w',encoding='utf-8') as f:
            while not done.is_set():
                while user.PeekMessageW(ctypes.byref(message),None,0,0,1):
                    user.TranslateMessage(ctypes.byref(message));user.DispatchMessageW(ctypes.byref(message))
                if active.is_set() and not notified:state('recording');notified=True
                while not events.empty():f.write(json.dumps(events.get(),ensure_ascii=False)+'\n')
                f.flush()
                now=time.perf_counter()
                if started[0] is not None and now-started[0]>=90:done.set()
                if started[0] is None and now-armed>=900:done.set()
                time.sleep(.003)
            done.set();observer.join(timeout=1)
            while not events.empty():f.write(json.dumps(events.get(),ensure_ascii=False)+'\n')
        state('finished',seconds=round(time.perf_counter()-started[0],3) if started[0] else 0,**counts)
    except Exception as e:state('error',message=str(e))
    finally:
        done.set()
        if handle:user.UnhookWindowsHookEx(handle)
        if reader:reader.close()

if __name__=='__main__':main()
