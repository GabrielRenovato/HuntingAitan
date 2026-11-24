"""Regras para a barra de Templario conferida localmente; nao remapeia teclas."""
import copy
from huntingaitan.configuracao.perfil_hunt import validar

ESPERADAS={'2':1057,'3':1146,'4':1258,'5':1320,'6':1394,'7':1334,'8':1379,'ctrl+1':1135,'ctrl+2':1242,'ctrl+3':1088}

def preparar(perfil,slots):
    barra={s['tecla']:s for s in slots if s.get('tecla')}
    for tecla,id_ in ESPERADAS.items():
        if barra.get(tecla,{}).get('skill_id')!=id_:
            raise ValueError('Barra diferente da conferida; reconfira a habilidade em '+tecla)
    p=copy.deepcopy(perfil)
    regras=[]
    def regra(tecla,tipo,**condicoes):
        s=barra[tecla]
        regras.append(dict(nome=s['nome'],tecla=tecla,tipo=tipo,skill_id=s['skill_id'],
                           mp_min=s['mana'],intervalo_s=condicoes.pop('intervalo_s',max(3,s['recarga_s'])),**condicoes))
    regra('ctrl+3','emergencia',hp_max_pct=p.get('hp_percent',70))
    regra('7','defesa',hp_max_pct=80,so_em_combate=True)
    # Roubo de vida precisa de dano causado; nao e uma cura instantanea.
    regra('3','buff',intervalo_s=3)
    regra('5','buff_combate',alcance_m=3,alvo_hp_min_pct=20)
    regra('8','buff_combate',alcance_m=3,mobs_min=2,mobs_raio_m=3,alvo_hp_min_pct=20)
    regra('2','ataque',alcance_m=2.4)
    regra('4','ataque',alcance_m=4,mobs_min=2,mobs_raio_m=4)
    regra('6','ataque',alcance_m=6,mobs_min=2,mobs_raio_m=6,alvo_hp_min_pct=20)
    p['reacoes']=regras
    # Remediar sai do rebuff periodico e passa a responder a vida.
    # Apenas os dois buffs realmente encontrados permanecem nessa agenda.
    p['buff_keys']=['ctrl+1','ctrl+2','','','']
    p['heal_enabled']=False
    for s in p['skills']:s['enabled']=False
    for campo in ('hp_keys','mp_keys'):
        p[campo]=['' if k in ESPERADAS else k for k in p[campo]]
    for s in p['items']:
        if s['key'] in ESPERADAS:s['enabled']=False
    return validar(p)

def ajustar_pve(perfil,slots):
    """Ajusta a barra confirmada sem substituir percurso, conta ou itens extras."""
    barra={s['tecla']:s for s in slots if s.get('tecla')}
    for tecla,id_ in ESPERADAS.items():
        if barra.get(tecla,{}).get('skill_id')!=id_:
            raise ValueError('Barra diferente da conferida; reconfira a habilidade em '+tecla)
    p=copy.deepcopy(perfil);regras=p.setdefault('reacoes',[])
    reserva=barra['ctrl+3']['mana']
    configuracoes=[
        ('ctrl+3','Remediar','emergencia',2.2,dict(hp_max_pct=70)),
        ('7','El Aegis','buff',3,{}),
        ('3','Sangue Sagrado','buff',3,{}),
        ('5','Thymos','buff_combate',3,{}),
        ('8','Lâmina da Promessa','buff_combate',3,dict(mobs_min=1,mobs_raio_m=3,alcance_m=3,alvo_hp_min_pct=10)),
        ('2','Perícia com Escudo','ataque',1.2,dict(alcance_m=2.4)),
        ('4','Emissão Divina','ataque',1.2,dict(mobs_min=1,mobs_raio_m=4,alcance_m=4)),
        ('6','Santuário','ataque',3,dict(mobs_min=1,mobs_raio_m=6,alcance_m=6,alvo_hp_min_pct=10)),
        ('ctrl+2','Proteção','buff',3,{})]
    for tecla,nome,tipo,intervalo,condicoes in configuracoes:
        s=barra[tecla];r=next((r for r in regras if r.get('skill_id')==s['skill_id']),None)
        if r is None:r={};regras.append(r)
        r.update(nome=nome,tecla=tecla,tipo=tipo,ativa=True,skill_id=s['skill_id'],hp_max_pct=100,
                 mp_max_pct=100,mp_min=s['mana']+(reserva if tipo in ('ataque','buff_combate') else 0),
                 so_em_combate=False,mobs_min=0,mobs_raio_m=6,alvo_hp_min_pct=0,alvo_hp_max_pct=100,
                 alcance_m=0,intervalo_s=intervalo)
        r.update(condicoes)
    # Pocao de vida instantanea ja configurada fica antes da cura conjurada.
    pocoes=[r for r in regras if r.get('tipo')=='item_hp' and r.get('ativa',True)]
    for r in pocoes:r['tipo']='emergencia'
    p['reacoes']=pocoes+[r for r in regras if r not in pocoes]
    usadas={r['tecla'] for r in p['reacoes'] if r.get('ativa',True)}
    p['buff_keys']=['' if k in usadas else k for k in p['buff_keys']]
    for campo in ('skills','items'):
        for s in p[campo]:
            if s['key'] in usadas:s['enabled']=False
    for k in ('hp_keys','mp_keys'):p[k]=['' if v in usadas else v for v in p[k]]
    p['heal_enabled']=False;p['action_gap']=.6
    return validar(p)
