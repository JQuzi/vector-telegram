# db_utils.py
"""""
Фасад для обратной совместимости.

Раньше весь доступ к БД был в одном файле db_utils.py.
Теперь логика разнесена по db/repositories/*, но хендлеры продолжают
импортировать db_utils как раньше: `import db_utils as db`.
"""

from db.repositories.users_repo import *   # noqa
from db.repositories.habits_repo import *  # noqa
from db.repositories.goals_repo import *   # noqa
from db.repositories.stats_repo import *   # noqa
from db.repositories.events_repo import *  # noqa

# Важно: внутренние helpers НЕ экспортируем наружу специально.
