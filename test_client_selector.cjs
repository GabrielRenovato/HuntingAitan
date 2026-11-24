const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const source=fs.readFileSync('aika_hunt_app/renderer.js','utf8');
function element(){return {options:[],value:'',textContent:'',disabled:false,replaceChildren(){this.options=[];},append(o){this.options.push(o);}};}
const elements=Object.fromEntries(['client-select','refresh-clients','client-state','player-read'].map(k=>[k,element()]));
const ctx=vm.createContext({document:{createElement:element},$:k=>elements[k],profile:{client_pid:200,client_hwnd:20},running:false,openClients:[{pid:100,hwnd:10,name:'DilmaRusef',exe:'AIKACL.exe',ready:true},{pid:200,hwnd:20,name:'Domination',exe:'AIKACL-multiinstancia-teste.exe',ready:true}]});
vm.runInContext(source.slice(source.indexOf('function renderClients(){'),source.indexOf('function baseLabel()')),ctx);
vm.runInContext('renderClients()',ctx);
assert.equal(elements['client-select'].value,'200:20');assert.equal(elements['player-read'].textContent,'Domination');
assert.match(elements['client-select'].options[2].textContent,/Domination.*200/);
vm.runInContext('running=true;renderClients()',ctx);assert.equal(elements['client-select'].disabled,true);assert.equal(elements['refresh-clients'].disabled,true);
vm.runInContext('running=false;openClients=[];renderClients()',ctx);
assert.equal(elements['client-select'].value,'200:20');assert.match(elements['client-state'].textContent,/não está aberto/);
console.log('OK: seletor distingue personagens, bloqueia troca durante a caça e preserva cliente fechado sem trocar de conta.');
