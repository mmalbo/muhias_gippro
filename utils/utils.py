import unicodedata
import uuid 

def eliminar_tildes(texto):
    # 'NFD' descompone los caracteres acentuados
    # 'Mn' significa Non-Spacing Marks (marcas diacríticas)
    return ''.join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    )

def normalizar_UUID(uuid_str):
    if not uuid_str:
        return None
    try:
        uuid_limpio = str(uuid_str).replace('-','').strip()
        if len(uuid_limpio) == 32:
            return uuid_limpio
        else:
            return str(uuid.UUID(uuid_str)).replace('-','')
    except (ValueError, TypeError):
        return uuid_str