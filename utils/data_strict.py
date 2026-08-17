from dataclasses import dataclass


@dataclass
class MessageAI:
    owner_id: int
    owner_name: str
    message: str
    time: str
    reference: "MessageAI | None" = None
    is_bot: bool = False

    def __repr__(self) -> str:
        return self.format_tree()

    def format_tree(self) -> str:
        nodes = []
        current = self
        while current:
            nodes.append(current)
            current = current.reference

        nodes.reverse()

        lines = []
        for depth, node in enumerate(nodes):
            spaces = "  " * depth
            lines.append(
                f"{spaces}-> {node.owner_name}|ID:{node.owner_id}|{node.time}: {node.message}"
            )

        return "\n".join(lines)

    def to_list(self) -> list["MessageAI"]:
        nodes = []
        current = self
        while current:
            nodes.append(current)
            current = current.reference

        nodes.reverse()
        return nodes

    def to_dict(self) -> dict:
        data = {
            "owner_id": self.owner_id,
            "owner_name": self.owner_name,
            "time": self.time,
            "message": self.message,
            "reference": None,
            "is_bot": self.is_bot,
        }
        if self.reference:
            data["reference"] = self.reference.to_dict()

        return data
