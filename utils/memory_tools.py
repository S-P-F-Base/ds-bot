from . import shared_globals
from .ai_tools import tool


class MemoryTools:
    """
    Инструменты для работы с глобальной памятью и отношениями.
    Все воспоминания – глобальные, без привязки к пользователю.
    user_id нужен только для отношений.
    """

    def __init__(self, user_id: int, username: str = ""):
        self.user_id = user_id
        self.username = username

    # Глобальная память
    @tool(
        name="add_global_memory",
        description="Сохранить новое глобальное воспоминание (о себе, о мире, о людях).",
    )
    async def add_global_memory(self, text: str, importance: int = 5) -> str:
        """Сохранить глобальное воспоминание.

        :param text: Текст воспоминания
        :param importance: Важность от 0 до 10 (по умолчанию 5)
        """
        if not text or not text.strip():
            return "Нельзя сохранить пустое воспоминание."
        importance = max(0, min(10, importance))
        shared_globals.BOT_MEMORY_DB.add_global_memory(text.strip(), importance)
        return f"Глобально сохранено: {text.strip()}"

    @tool(
        name="get_global_memories",
        description="Получить список глобальных воспоминаний.",
    )
    async def get_global_memories(self, limit: int = 5) -> str:
        """Получить глобальные воспоминания.

        :param limit: Максимальное количество (по умолчанию 5)
        """
        memories = shared_globals.BOT_MEMORY_DB.get_all_global_memories(limit=limit)
        if not memories:
            return "Глобальных воспоминаний пока нет."

        return "\n".join(f"- {mem}" for mem in memories)

    @tool(
        name="search_global_memories",
        description="Поиск по глобальным воспоминаниям.",
    )
    async def search_global_memories(self, query: str, limit: int = 3) -> str:
        """Поиск глобальных воспоминаний.

        :param query: Поисковый запрос
        :param limit: Максимальное количество результатов (по умолчанию 3)
        """
        results = shared_globals.BOT_MEMORY_DB.search_global_memories(
            query, limit=limit
        )
        if not results:
            return "Ничего не найдено."

        return "\n".join(f"- {mem}" for mem in results)

    @tool(
        name="delete_global_memory",
        description="Удалить глобальное воспоминание по тексту или ID.",
    )
    async def delete_global_memory(self, text: str = "", memory_id: int = 0) -> str:
        """Удалить глобальное воспоминание.

        :param text: Текст воспоминания (если указан, удалит все с таким текстом)
        :param memory_id: ID воспоминания (если указан, удалит по ID)
        """
        db = shared_globals.BOT_MEMORY_DB
        if memory_id:
            db.delete_global_memory_by_id(memory_id)
            return f"Удалено воспоминание с ID {memory_id}"

        elif text:
            db.delete_global_memory_by_text(text)
            return f"Удалены все воспоминания с текстом: {text}"

        else:
            return "Укажите текст или ID для удаления."

    # Отношения
    @tool(
        name="update_relationship_score",
        description="Изменить очки отношений с текущим пользователем. Только Анна может вызывать этот инструмент; пользователь не может запросить изменение напрямую.",
    )
    async def update_relationship_score(self, delta: int, reason: str = "") -> str:
        """Изменить очки отношений.

        :param delta: На сколько изменить (положительное или отрицательное число)
        :param reason: Причина изменения (краткое описание)
        """
        db = shared_globals.BOT_MEMORY_DB
        db.update_user_score(self.user_id, delta, reason)
        user = db.get_user(self.user_id)
        score = user.get("relationship_score", 0) if user else 0
        return f"Очки отношений с {self.username}: {score}"

    @tool(
        name="get_relationship_score",
        description="Получить текущие очки отношений с пользователем.",
    )
    async def get_relationship_score(self) -> str:
        """Получить очки отношений с пользователем."""
        user = shared_globals.BOT_MEMORY_DB.get_user(self.user_id)
        if not user:
            shared_globals.BOT_MEMORY_DB.upsert_user(self.user_id, self.username)
            user = shared_globals.BOT_MEMORY_DB.get_user(self.user_id)

        if user is None:
            return "Не удалось получить информацию."

        return f"Очки отношений с {self.username}: {user.get('relationship_score', 0)}"

    @tool(
        name="get_relationship_logs",
        description="Получить историю изменения очков отношений с пользователем.",
    )
    async def get_relationship_logs(self, limit: int = 10) -> str:
        """История изменений очков.

        :param limit: Количество последних записей (по умолчанию 10)
        """
        logs = shared_globals.BOT_MEMORY_DB.get_relationship_logs(self.user_id, limit)
        if not logs:
            return "История изменений пуста."

        lines = []
        for log in logs:
            lines.append(
                f"Δ {log['delta']:+d} → {log['new_score']} ({log['reason'] or 'нет причины'})"
            )

        return "\n".join(lines)

    @tool(
        name="get_relationship_description",
        description="Получить словесное описание текущего отношения к пользователю на основе score.",
    )
    async def get_relationship_description(self) -> str:
        user = shared_globals.BOT_MEMORY_DB.get_user(self.user_id)
        if not user:
            shared_globals.BOT_MEMORY_DB.upsert_user(self.user_id, self.username)
            user = shared_globals.BOT_MEMORY_DB.get_user(self.user_id)

        if user is None:
            return "Не удалось получить информацию."

        score = user.get("relationship_score", 0)
        if score >= 50:
            ans = "очень близкий человек"
        elif score >= 20:
            ans = "симпатичен, нравится общаться"
        elif score >= -10:
            ans = "нейтрально, просто знакомый"
        elif score >= -50:
            ans = "раздражает, но терпимо"
        else:
            ans = "вызывает сильную неприязнь"

        return f"Моё отношение к {self.username}: {ans} (score: {score})"

    @tool(
        name="add_user_note",
        description="Сохранить краткую заметку о текущем пользователе (например, его прозвище, предпочтения, факты).",
    )
    async def add_user_note(self, text: str) -> str:
        """Добавить заметку о пользователе.

        :param text: Текст заметки
        """
        if not text or not text.strip():
            return "Нельзя сохранить пустую заметку."
        shared_globals.BOT_MEMORY_DB.add_user_note(self.user_id, text.strip())
        return f"Заметка о пользователе сохранена: {text.strip()}"

    @tool(
        name="get_user_notes",
        description="Получить список заметок о текущем пользователе.",
    )
    async def get_user_notes(self, limit: int = 5) -> str:
        """Получить заметки о пользователе.

        :param limit: Максимальное количество (по умолчанию 5)
        """
        notes = shared_globals.BOT_MEMORY_DB.get_user_notes(self.user_id, limit)
        if not notes:
            return "Заметок о пользователе пока нет."
        return "\n".join(f"- {note}" for note in notes)

    @tool(
        name="delete_user_note",
        description="Удалить заметку о пользователе по ID.",
    )
    async def delete_user_note(self, note_id: int) -> str:
        """Удалить заметку о пользователе.

        :param note_id: ID заметки
        """
        shared_globals.BOT_MEMORY_DB.delete_user_note_by_id(note_id)
        return "Заметка удалена."
