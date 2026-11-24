const {contextBridge,ipcRenderer}=require('electron');
contextBridge.exposeInMainWorld('hunt',Object.freeze({
 info:()=>ipcRenderer.invoke('app:info'),checkUpdates:()=>ipcRenderer.invoke('updates:check'),
 load:()=>ipcRenderer.invoke('profile:load'),save:p=>ipcRenderer.invoke('profile:save',p),
 clients:()=>ipcRenderer.invoke('clients:list'),position:p=>ipcRenderer.invoke('data:position',p),bar:p=>ipcRenderer.invoke('data:barra',p),native:p=>ipcRenderer.invoke('profile:native',p),
 start:p=>ipcRenderer.invoke('hunt:start',p),stop:()=>ipcRenderer.invoke('hunt:stop'),pause:v=>ipcRenderer.invoke('hunt:pause',v),
 minimize:()=>ipcRenderer.invoke('window:minimize'),close:()=>ipcRenderer.invoke('window:close'),logs:()=>ipcRenderer.invoke('logs:open'),
 flowEditor:aberto=>ipcRenderer.invoke('window:flow-editor',aberto),
 onEvent:callback=>{const handler=(_,e)=>callback(e);ipcRenderer.on('hunt:event',handler);return()=>ipcRenderer.removeListener('hunt:event',handler);}
}));
