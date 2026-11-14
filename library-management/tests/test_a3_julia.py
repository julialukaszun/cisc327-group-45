from unittest.mock import patch

import pytest

from app import store
from app.models.book import Book
from app.models.member import Member

SEND = "app.routes.loans.send_notification"

@pytest.fixture
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