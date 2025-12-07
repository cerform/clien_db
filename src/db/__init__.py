try:
    from . import db
    from . import services
    from . import calendars
    __all__ = ['db', 'services', 'calendars']
except ImportError:
    # Если импорт не удался, продолжаем без них
    __all__ = []
