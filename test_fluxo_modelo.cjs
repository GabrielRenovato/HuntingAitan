const assert=require('node:assert/strict');const M=require('./aika_hunt_app/fluxo-modelo.js');
const cura={...M.PADRAO,nome:'Remediar',tecla:'ctrl+3',tipo:'cura',hp_max_pct:70,mp_min:1497,skill_id:1088,intervalo_s:3};
const graph=M.criar(cura);assert.deepEqual(M.compilar(graph),cura);
const quebrado=structuredClone(graph);quebrado.edges.pop();assert.throws(()=>M.compilar(quebrado),/Conecte|caminho|desconectado/);
const ciclico=structuredClone(graph);M.conectar(ciclico,'pronta','hp');assert(M.validar(ciclico).length);
M.remover(graph,'hp');assert.equal(M.compilar(graph).hp_max_pct,100);
console.log('OK: importa e compila cura sem perda, rejeita conexao quebrada/ciclo e remove condicao.');
for(const tipo of ['emergencia','defesa','cura','item_hp','item_mp','buff_combate','ataque']){
 const r={...M.PADRAO,nome:tipo,tipo,tecla:'f2',mp_min:1497,mobs_min:2,mobs_raio_m:4,alcance_m:2.4,alvo_hp_min_pct:10,alvo_hp_max_pct:80,so_em_combate:true};
 assert.deepEqual(M.compilar(M.criar(r)),r);
}
const decimal=M.criar({...cura,alcance_m:2.4});assert.equal(M.compilar(decimal).alcance_m,2.4);
const limite=structuredClone(decimal);limite.nodes.find(n=>n.type==='alcance').data.value=40.1;assert.throws(()=>M.compilar(limite),/entre 0 e 40/);
const incompat=M.criar({...cura,tipo:'item_mp'});incompat.nodes.find(n=>n.type==='mp_pct').type='hp';assert(M.validar(incompat).some(e=>e.message.includes('Item de mana')));
console.log('OK: sete tipos preservados e limites/condicoes incompativeis rejeitados.');
