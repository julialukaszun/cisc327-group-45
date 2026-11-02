import json
from datetime import datetime, timezone
from pathlib import Path


class Backup: # Represents one snapshot
    def __init__(self, books, members, updated_at=None):
        self.books = books
        self.members = members
        self.updated_at = updated_at or datetime.now(timezone.utc).isoformat() # Supplying timestamp is optional

    @classmethod
    def from_store(cls, books, members): # Creates snapshot from stored objects
        return cls( # Returns a backup object
            books=[book.to_dict() for book in books],
            members=[member.to_dict() for member in members],
        )

    @classmethod
    def load(cls, file_path): # Reads previously saved snapshot
        data = json.loads(Path(file_path).read_text(encoding="utf-8"))
        return cls( # Returns backup from saved fields
            books=data["books"],
            members=data["members"],
            updated_at=data["updated_at"],
        )

    def save(self, file_path): # Writes snapshot to a file
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True) # If parent directories missing, this makes them
        path.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")

    def to_dict(self): # Returns snapshot in dictionary for json output
        return {
            "updated_at": self.updated_at,
            "books": self.books,
            "members": self.members,
        }
