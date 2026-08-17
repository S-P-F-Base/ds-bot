from . import shared_globals
from .ai_tools import tool


class MemoryTools:
    """
    Инструменты для работы с памятью пользователя.
    При создании экземпляра передаётся user_id, и все методы используют его.
    """

    def __init__(self, user_id: int, username: str = ""):
        self.user_id = user_id
        self.username = username

    @tool(
        name="get_memories",
        description="Получить список сохранённых воспоминаний о пользователе.",
    )
    async def get_memories(self, limit: int = 5) -> str:
        """Получить последние воспоминания.

        :param limit: Максимальное количество воспоминаний (по умолчанию 5)
        """
        memories = shared_globals.BOT_MEMORY_DB.get_all_memories(
            self.user_id, limit=limit
        )
        if not memories:
            return "Пока нет сохранённых воспоминаний."
        return "\n".join(f"- {mem}" for mem in memories)

    @tool(
        name="add_memory",
        description="Сохранить новое воспоминание о пользователе.",
    )
    async def add_memory(self, text: str, importance: int = 5) -> str:
        """Добавить воспоминание.

        :param text: Текст воспоминания
        :param importance: Важность от 0 до 10 (по умолчанию 5)
        """
        if not text or not text.strip():
            return "Нельзя сохранить пустое воспоминание."
        importance = max(0, min(10, importance))
        shared_globals.BOT_MEMORY_DB.add_memory(self.user_id, text.strip(), importance)
        return f"Сохранено: {text.strip()}"

    @tool(
        name="search_memories",
        description="Поиск по сохранённым воспоминаниям.",
    )
    async def search_memories(self, query: str, limit: int = 3) -> str:
        """Поиск воспоминаний по ключевому слову.

        :param query: Поисковый запрос
        :param limit: Максимальное количество результатов (по умолчанию 3)
        """
        results = shared_globals.BOT_MEMORY_DB.search_memories(
            self.user_id, query, limit=limit
        )
        if not results:
            return "Ничего не найдено."
        return "\n".join(f"- {mem}" for mem in results)

    @tool(
        name="delete_memory",
        description="Удалить воспоминание по его ID.",
    )
    async def delete_memory(self, memory_id: int) -> str:
        """Удалить воспоминание.

        :param memory_id: ID воспоминания (можно узнать через get_memories)
        """
        memory = shared_globals.BOT_MEMORY_DB.get_memory_by_id(memory_id)
        if not memory or memory["user_id"] != self.user_id:
            return "Воспоминание не найдено или у вас нет прав на его удаление."
        shared_globals.BOT_MEMORY_DB.delete_memory(memory_id)
        return "Воспоминание удалено."

    @tool(
        name="get_user_info",
        description="Получить информацию о пользователе (имя, очки отношений).",
    )
    async def get_user_info(self) -> str:
        """Получить информацию о пользователе."""
        user = shared_globals.BOT_MEMORY_DB.get_user(self.user_id)
        if not user:
            shared_globals.BOT_MEMORY_DB.upsert_user(self.user_id, self.username)
            user = shared_globals.BOT_MEMORY_DB.get_user(self.user_id)

        if user is None:
            return "Не удалось получить информацию о пользователе."

        return (
            f"Имя: {user.get('username', 'неизвестно')}, "
            f"очки отношений: {user.get('relationship_score', 0)}"
        )
