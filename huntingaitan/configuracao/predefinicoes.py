"""Predefinicoes de reacoes de sobrevivencia por classe, para aplicar ao perfil do painel."""
import copy,json,time
from pathlib import Path
from huntingaitan.configuracao.perfil_hunt import validar

# Remediar (id 1088, nivel 16): cura em 2 s de conjuracao e 1497 de mana; usar quando a vida chega a 40%.
TEMPLARIO=[
    dict(nome='Remediar',tecla='f2',tipo='cura',skill_id=1088,hp_max_pct=40,mp_min=1497,intervalo_s=2.5),
]

PREDEFINICOES={'templario':TEMPLARIO}

def aplicar(perfil,nome='templario'):
    """Perfil validado com as reacoes da predefinicao. As reacoes anteriores sao substituidas."""
    novo=copy.deepcopy(perfil);novo['reacoes']=copy.deepcopy(PREDEFINICOES[nome])
    return validar(novo)

def aplicar_em_arquivo(caminho,nome='templario',agora=time.strftime):
    """Le o profile.json, guarda uma copia e grava o perfil com a predefinicao. Devolve o perfil gravado."""
    caminho=Path(caminho);original=json.loads(caminho.read_text(encoding='utf-8'))
    resultado=aplicar(original,nome)
    copia=caminho.with_name(f'profile.antes_reacoes_{agora("%Y%m%d_%H%M%S")}.json')
    copia.write_text(json.dumps(original,indent=2,ensure_ascii=False),encoding='utf-8')
    temporario=caminho.with_suffix('.json.tmp')
    temporario.write_text(json.dumps(resultado,indent=2,ensure_ascii=False),encoding='utf-8');temporario.replace(caminho)
    return resultado
