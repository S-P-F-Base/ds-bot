from datetime import UTC, datetime

import dataset


class MemoryDB:
    DB_PATH = "sqlite:///memory.db"

    def __init__(self):
        self.db = dataset.connect(self.DB_PATH)
        self._init_tables()

    def _init_tables(self):
        self.users = self.db.create_table("users")
        self.users.create_column("user_id", self.db.types.integer)
        self.users.create_column("username", self.db.types.string)
        self.users.create_column("relationship_score", self.db.types.integer, default=0)
        self.users.create_column("last_seen", self.db.types.datetime)

        self.global_memories = self.db.create_table("global_memories")
        self.global_memories.create_column(
            "id", self.db.types.integer, primary_key=True, autoincrement=True
        )
        self.global_memories.create_column("text", self.db.types.string)
        self.global_memories.create_column(
            "importance", self.db.types.integer, default=5
        )
        self.global_memories.create_column("created_at", self.db.types.datetime)
        self.global_memories.create_column("updated_at", self.db.types.datetime)

        self.relationship_logs = self.db.create_table("relationship_logs")
        self.relationship_logs.create_column(
            "id", self.db.types.integer, primary_key=True, autoincrement=True
        )
        self.relationship_logs.create_column("user_id", self.db.types.integer)
        self.relationship_logs.create_column("delta", self.db.types.integer)
        self.relationship_logs.create_column("new_score", self.db.types.integer)
        self.relationship_logs.create_column("reason", self.db.types.string)
        self.relationship_logs.create_column("created_at", self.db.types.datetime)

        self.user_notes = self.db.create_table("user_notes")
        self.user_notes.create_column(
            "id", self.db.types.integer, primary_key=True, autoincrement=True
        )
        self.user_notes.create_column("user_id", self.db.types.integer)
        self.user_notes.create_column("text", self.db.types.string)
        self.user_notes.create_column("created_at", self.db.types.datetime)

    # Глобальная память
    def add_global_memory(self, text: str, importance: int = 5):
        self.global_memories.insert(
            {
                "text": text,
                "importance": max(0, min(10, importance)),
                "created_at": datetime.now(UTC),
                "updated_at": datetime.now(UTC),
            }
        )

    def search_global_memories(self, query: str, limit: int = 5) -> list[str]:
        rows = self.global_memories.find(text={"ilike": f"%{query}%"}, _limit=limit)
        return [row["text"] for row in rows]

    def get_all_global_memories(self, limit: int = 10) -> list[str]:
        rows = self.global_memories.find(_limit=limit, order_by="-importance")
        return [row["text"] for row in rows]

    def delete_global_memory_by_id(self, memory_id: int):
        self.global_memories.delete(id=memory_id)

    def delete_global_memory_by_text(self, text: str):
        rows = self.global_memories.find(text=text)
        for row in rows:
            self.global_memories.delete(id=row["id"])

    # Пользователи и отношения
    def get_user(self, user_id: int) -> dict | None:
        row = self.users.find_one(user_id=user_id)
        return dict(row) if row else None

    def upsert_user(self, user_id: int, username: str):
        current = self.get_user(user_id)
        if current is None:
            self.users.insert(
                {
                    "user_id": user_id,
                    "username": username,
                    "relationship_score": 0,
                    "last_seen": datetime.now(UTC),
                }
            )

        else:
            self.users.update(
                {
                    "user_id": user_id,
                    "username": username,
                    "last_seen": datetime.now(UTC),
                },
                ["user_id"],
            )

    def update_user_score(self, user_id: int, delta: int, reason: str = ""):
        current = self.get_user(user_id)
        current_score = 0
        if current:
            current_score = current.get("relationship_score")
            current_score = int(current_score) if current_score is not None else 0

        new_score = current_score + delta
        new_score = max(-100, min(100, new_score))

        if current:
            self.users.update(
                {"user_id": user_id, "relationship_score": new_score}, ["user_id"]
            )

        else:
            self.users.insert(
                {
                    "user_id": user_id,
                    "username": "",
                    "relationship_score": new_score,
                    "last_seen": datetime.now(UTC),
                }
            )

        self.relationship_logs.insert(
            {
                "user_id": user_id,
                "delta": delta,
                "new_score": new_score,
                "reason": reason,
                "created_at": datetime.now(UTC),
            }
        )

    def get_relationship_logs(self, user_id: int, limit: int = 10) -> list[dict]:
        rows = self.relationship_logs.find(
            user_id=user_id, _limit=limit, order_by="-id"
        )
        return [dict(row) for row in rows]

    def add_user_note(self, user_id: int, text: str):
        self.user_notes.insert(
            {
                "user_id": user_id,
                "text": text,
                "created_at": datetime.now(UTC),
            }
        )

    def get_user_notes(self, user_id: int, limit: int = 5) -> list[dict]:
        rows = self.user_notes.find(user_id=user_id, _limit=limit, order_by="-id")
        return [{"id": row["id"], "text": row["text"]} for row in rows]

    def delete_user_note_by_text(self, user_id: int, text: str):
        rows = self.user_notes.find(user_id=user_id, text=text)
        for row in rows:
            self.user_notes.delete(id=row["id"])

    def delete_user_note_by_id(self, note_id: int):
        self.user_notes.delete(id=note_id)
