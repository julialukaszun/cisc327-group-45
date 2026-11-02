from flask import Blueprint, current_app, jsonify, request

from app import store
from app.models.backup import Backup
from app.models.book import Book

books_bp = Blueprint("books", __name__, url_prefix="/books")

# improved functionalitiy: added the ability to search by Book ID and ISBN
@books_bp.route("", methods=["GET"])
def list_books():
    results = list(store.books.values())

    search = request.args.get("search", "").strip().lower()
    if search:
        search_isbn = search.replace("-", "").replace(" ", "")
        results = [
            b for b in results
            if (search.isdecimal() and b.id == int(search))
            or (search_isbn and b.isbn.replace("-", "").lower() == search_isbn)
            or search in b.title.lower()
            or search in b.author.lower()
        ]

    return jsonify([b.to_dict() for b in results])


@books_bp.route("", methods=["POST"])
def create_book():
    data = request.get_json()
    book_id = store.next_id("book")
    book = Book(
        id=book_id,
        title=data["title"],
        author=data["author"],
        isbn=data["isbn"],
        total_copies=data.get("total_copies", 1),
        available_copies=data.get("total_copies", 1),
    )
    store.books[book_id] = book

    # Creates snapshot and writes it to backup file
    Backup.from_store(store.books.values(), store.members.values()).save(
        current_app.config["BACKUP_FILE"]
    )
    return jsonify(book.to_dict()), 201


@books_bp.route("/<int:book_id>", methods=["GET"])
def get_book(book_id):
    book = store.books.get(book_id)
    if book is None:
        return jsonify({"error": "Book not found"}), 404
    return jsonify(book.to_dict())


@books_bp.route("/<int:book_id>", methods=["PUT"])
def update_book(book_id):
    book = store.books.get(book_id)
    if book is None:
        return jsonify({"error": "Book not found"}), 404
    data = request.get_json()
    book.title = data.get("title", book.title)
    book.author = data.get("author", book.author)
    book.isbn = data.get("isbn", book.isbn)
    book.total_copies = data.get("total_copies", book.total_copies)
    book.available_copies = data.get("available_copies", book.available_copies)

     # Creates snapshot and writes it to backup file
    Backup.from_store(store.books.values(), store.members.values()).save(
        current_app.config["BACKUP_FILE"]
    )
    return jsonify(book.to_dict())


@books_bp.route("/<int:book_id>", methods=["DELETE"])
def delete_book(book_id):
    book = store.books.pop(book_id, None)
    if book is None:
        return jsonify({"error": "Book not found"}), 404

    # Creates snapshot and writes it to backup file
    Backup.from_store(store.books.values(), store.members.values()).save(
        current_app.config["BACKUP_FILE"]
    )
    return "", 204
