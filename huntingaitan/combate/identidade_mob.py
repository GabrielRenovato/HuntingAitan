"""Identidade da especie separada do ID de instancia, conforme o cliente validado."""
import unicodedata

VERIT_MUTANTE=1378

def verit_mutante(mob):
    if not mob:return False
    codigo=mob.get('template_id')
    if codigo is not None:return codigo==VERIT_MUTANTE
    # Replays antigos nao possuem o campo descoberto. Mantem compatibilidade
    # sem fazer um nome contradizer um codigo de especie disponivel.
    nome=''.join(c for c in unicodedata.normalize('NFKD',mob.get('name','').lower()) if c.isalpha())
    return nome=='veritmutante'
