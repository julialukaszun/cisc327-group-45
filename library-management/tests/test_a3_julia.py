from datetime import date
from unittest.mock import patch

import pytest

from app import store
from app.models.book import Book
from app.models.loan import Loan
from app.models.member import Member

SEND = "app.routes.loans.send_notification"

@pytest.fixture # for notification tests
def book_and_member():
    """Create one book (1 copy) and one member with an email directly in the store."""
    store.books.clear()
    store.members.clear()
    store.loans.clear()

    book = Book(id=1, title="Clean Code", author="Robert C. Martin", isbn="978-0132350884",
            total_copies=1, available_copies=1)
    member = Member(id=1, name="Ada", email="ada@example.com")

    store.books[book.id] = book
    store.members[member.id] = member
    return book, member

@pytest.fixture # for coverage-directed tests
def empty_store():
    store.books.clear()
    store.members.clear()
    store.loans.clear()
    yield
    store.books.clear()
    store.members.clear()
    store.loans.clear()

# helpers for coverage-directed tests
def _add_book(book_id=1, title="Clean Code", copies=2):
    book = Book(id=book_id, title=title, author="Robert C. Martin", isbn="978-0132350884",
                total_copies=copies, available_copies=copies)
    store.books[book_id] = book
    return book


def _add_member(member_id=1, name="Ada", email="ada@example.com"):
    member = Member(id=member_id, name=name, email=email)
    store.members[member_id] = member
    return member


def _add_loan(loan_id=1, book_id=1, member_id=1):
    loan = Loan(id=loan_id, book_id=book_id, member_id=member_id,
                due_date=Loan.default_due_date())
    store.loans[loan_id] = loan
    return loan

# tests for notification service (success path)
def test_checkout_succeeds_when_notification_stub_returns_true(client, book_and_member, monkeypatch): #stub
    book, member = book_and_member
    monkeypatch.setattr(SEND, lambda recipient, subject, message: True)

    resp = client.post("/loans", json={"book_id": book.id, "member_id": member.id})

    assert resp.status_code == 201
    data = resp.get_json()
    assert data["notification_sent"] is True
    assert data["book_id"] == book.id
    assert data["member_id"] == member.id
    assert data["id"] in store.loans
    assert store.loans[data["id"]].return_date is None


def test_checkout_sends_loan_confirmation_with_expected_arguments(client, book_and_member): #mock
    book, member = book_and_member
    copies_before = book.available_copies

    with patch(SEND, return_value=True) as mock_send:
        resp = client.post("/loans", json={"book_id": book.id, "member_id": member.id})

    assert resp.status_code == 201
    data = resp.get_json()
    loan = store.loans[data["id"]]

    assert data["notification_sent"] is True
    assert store.books[book.id].available_copies == copies_before - 1

    mock_send.assert_called_once_with(
        member.email,
        "[City Library] Loan confirmation",
        f"You borrowed '{book.title}'. It is due on {loan.due_date}.",
    )
    
# views.py/home
def test_home_page_renders_html(client, empty_store):
    resp = client.get("/")
    assert resp.status_code == 200
    assert "text/html" in resp.content_type
    assert len(resp.data) > 0

# views.py/books_page
def test_books_page_lists_existing_books(client, empty_store):
    _add_book(1, title="Clean Code")
    _add_book(2, title="Bad Code")
    resp = client.get("/ui/books")
    assert resp.status_code == 200
    assert b"Clean Code" in resp.data
    assert b"Bad Code" in resp.data

def test_add_book_form_creates_book_with_all_copies_available(client, empty_store):
    resp = client.post("/ui/books", data={
        "title": "Clean Code", "author": "Robert C. Martin", "isbn": "978-0132350884", "total_copies": "3",
    })
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/ui/books")
    assert len(store.books) == 1
    book = list(store.books.values())[0]
    assert book.title == "Clean Code"
    assert book.total_copies == 3
    assert book.available_copies == 3

def test_add_book_form_missing_title_is_rejected(client, empty_store):
    resp = client.post("/ui/books", data={
        "author": "Robert C. Martin", "isbn": "978-0132350884", "total_copies": "3",
    })
    assert resp.status_code == 400
    assert len(store.books) == 0

# views.py/delete_book_page
def test_delete_member_removes_only_that_member(client, empty_store):
    _add_member(1, name="Julia")
    _add_member(2, name="Bob")
    resp = client.post("/ui/members/1/delete")
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/ui/members")
    assert 1 not in store.members
    assert 2 in store.members

def test_delete_nonexistent_member_changes_nothing(client, empty_store):
    _add_member(1, name="Julia")
    resp = client.post("/ui/members/999/delete")
    assert resp.status_code == 302
    assert list(store.members.keys()) == [1]
    
# views.py/loans_page

def test_loans_page_shows_return_button_only_for_open_loans(client, empty_store):
    _add_book(1)
    _add_member(1)
    _add_loan(1)
    returned = _add_loan(2)
    returned.return_date = date.today()
    resp = client.get("/ui/loans")
    assert resp.status_code == 200
    assert b"/ui/loans/1/return" in resp.data
    assert b"/ui/loans/2/return" not in resp.data

def test_checkout_form_creates_loan_and_decrements_copies(client, empty_store):
    _add_book(1, copies=2)
    _add_member(1)
    resp = client.post("/ui/loans", data={"book_id": "1", "member_id": "1"})
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/ui/loans")
    assert len(store.loans) == 1
    loan = list(store.loans.values())[0]
    assert loan.book_id == 1
    assert loan.member_id == 1
    assert loan.return_date is None
    assert store.books[1].available_copies == 1

def test_checkout_form_unknown_book_creates_no_loan(client, empty_store):
    _add_book(1, copies=2)
    _add_member(1)
    resp = client.post("/ui/loans", data={"book_id": "999", "member_id": "1"})
    assert resp.status_code == 302
    assert len(store.loans) == 0
    assert store.books[1].available_copies == 2

# views.py/return_loan_page
def test_return_form_sets_return_date_and_restores_copy(client, empty_store):
    book = _add_book(1, copies=2)
    book.available_copies = 1
    _add_member(1)
    loan = _add_loan(1)
    resp = client.post("/ui/loans/1/return")
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/ui/loans")
    assert loan.return_date == date.today()
    assert store.books[1].available_copies == 2

def test_return_form_already_returned_loan_is_not_counted_twice(client, empty_store):
    book = _add_book(1, copies=2)
    book.available_copies = 2
    loan = _add_loan(1)
    original = date(2026, 1, 1)
    loan.return_date = original
    resp = client.post("/ui/loans/1/return")
    assert resp.status_code == 302
    assert loan.return_date == original
    assert store.books[1].available_copies == 2

def test_return_form_unknown_loan_changes_nothing(client, empty_store):
    book = _add_book(1, copies=2)
    book.available_copies = 1
    resp = client.post("/ui/loans/999/return")
    assert resp.status_code == 302
    assert store.books[1].available_copies == 1