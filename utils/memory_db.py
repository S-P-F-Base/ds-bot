from datetime import datetime
from typing import Dict, List, Optional

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

        self.memories = self.db.create_table("memories")
        self.memories.create_column(
            "id", self.db.types.integer, primary=True, autoincrement=True
        )
        self.memories.create_column("user_id", self.db.types.integer)
        self.memories.create_column("text", self.db.types.string)
        self.memories.create_column(
            "importance", self.db.types.integer, default=5
        )  # 0..10
        self.memories.create_column("created_at", self.db.types.datetime)
        self.memories.create_column("updated_at", self.db.types.datetime)

    def get_user(self, user_id: int) -> Optional[Dict]:
        row = self.users.find_one(user_id=user_id)
        return dict(row) if row else None

    def upsert_user(self, user_id: int, username: str):
        self.users.upsert(
            {"user_id": user_id, "username": username, "last_seen": datetime.now()},
            ["user_id"],
        )

    def update_user_score(self, user_id: int, delta: int):
        current = self.get_user(user_id)
        if current:
            new_score = current["relationship_score"] + delta

        else:
            new_score = delta

        self.users.update(
            {"user_id": user_id, "relationship_score": new_score}, ["user_id"]
        )

    def add_memory(self, user_id: int, text: str, importance: int = 5):
        self.memories.insert(
            {
                "user_id": user_id,
                "text": text,
                "importance": max(0, min(10, importance)),
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
            }
        )

    def search_memories(self, user_id: int, query: str, limit: int = 5) -> List[str]:
        rows = self.memories.find(
            user_id=user_id, text={"ilike": f"%{query}%"}, _limit=limit
        )
        return [row["text"] for row in rows]

    def get_all_memories(self, user_id: int, limit: int = 10) -> List[str]:
        rows = self.memories.find(user_id=user_id, _limit=limit, order_by="-importance")
        return [row["text"] for row in rows]

    def delete_memory(self, memory_id: int):
        self.memories.delete(id=memory_id)

    def get_memory_by_id(self, memory_id: int) -> Optional[Dict]:
        row = self.memories.find_one(id=memory_id)
        return dict(row) if row else None
