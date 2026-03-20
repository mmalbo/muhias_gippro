import unicodedata

def eliminar_tildes(texto):
    # 'NFD' descompone los caracteres acentuados
    # 'Mn' significa Non-Spacing Marks (marcas diacríticas)
    return ''.join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    )