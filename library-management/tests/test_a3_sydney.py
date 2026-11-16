from unittest.mock import patch
import pytest
from datetime import date, timedelta

from app import store
'''
Notification Failure Cases
'''

SEND = "app.routes.loans.send_notification"


def test_checkout_succeeds_when_notification_stub_returns_false(client, monkeypatch):
    member_response = client.post(
        "/members",
        json={"name": "Ada", "email": "ada@example.com"},
    )

    book_response = client.post(
        "/books",
        json={
            "title": "Clean Code",
            "author": "Robert C. Martin",
            "isbn": "978-0132350884",
            "total_copies": 1,
        },
    )

    member_id = member_response.get_json()["id"]
    book_id = book_response.get_json()["id"]
    monkeypatch.setattr(SEND, lambda recipient, subject, message: False)

    response = client.post(
        "/loans",
        json={"book_id": book_id, "member_id": member_id},
    )

    assert response.status_code == 201
    data = response.get_json()
    assert data["notification_sent"] is False
    assert data["book_id"] == book_id
    assert data["member_id"] == member_id


def test_checkout_does_not_notify_when_member_is_missing(client):
    book_response = client.post(
        "/books",
        json={
            "title": "Clean Code",
            "author": "Robert C. Martin",
            "isbn": "978-0132350884",
            "total_copies": 1,
        },
    )

    book_id = book_response.get_json()["id"]

    with patch(SEND) as mock_send:
        response = client.post(
            "/loans",
            json={"book_id": book_id, "member_id": 999},
        )

    assert response.status_code == 201
    assert response.get_json()["notification_sent"] is False
    mock_send.assert_not_called()



'''
Function: create_reservation
'''

def test_create_reservation_returns_created_reservation(client):
	member = client.post(
		"/members",
		json={"name": "Alice", "email": "alice3@gmail.com"}
	).get_json()
	book = client.post(
		"/books",
		json={
			"title": "Test Book",
			"author": "Test Author",
			"isbn": "1234567890",
			"total_copies": 1
		}
	).get_json()

	response = client.post(
		"/reservations",
		json={"book_id": book["id"], "member_id": member["id"]}
	)

	assert response.status_code == 201
	reservation = response.get_json()
	assert reservation["id"] == 1
	assert reservation["book_id"] == book["id"]
	assert reservation["member_id"] == member["id"]
	assert reservation["reservation_date"]
	assert reservation["fulfilled"] is False


def test_create_reservation_with_nonexistent_book_returns_error(client):
	member = client.post(
		"/members",
		json={"name": "Alice", "email": "alice3@gmail.com"}
	).get_json()

	response = client.post(
		"/reservations",
		json={"book_id": 999, "member_id": member["id"]}
	)

	assert response.status_code == 404
	assert response.get_json() == {"error": "Book not found"}


def test_create_reservation_with_nonexistent_member_returns_error(client):
	book = client.post(
		"/books",
		json={
			"title": "Test Book",
			"author": "Test Author",
			"isbn": "1234567890",
			"total_copies": 1
		}
	).get_json()

	response = client.post(
		"/reservations",
		json={"book_id": book["id"], "member_id": 999}
	)

	assert response.status_code == 404
	assert response.get_json() == {"error": "Member not found"}


def test_create_reservation_when_no_copies_are_available(client):
	member = client.post(
		"/members",
		json={"name": "Alice", "email": "alice3@gmail.com"}
	).get_json()

	book = client.post(
		"/books",
		json={
			"title": "Unavailable Book",
			"author": "Test Author",
			"isbn": "1234567890",
			"total_copies": 0
		}
	).get_json()

	response = client.post(
		"/reservations",
		json={"book_id": book["id"], "member_id": member["id"]}
	)

	assert response.status_code == 201
	assert response.get_json()["fulfilled"] is False
	assert client.get(f"/books/{book['id']}").get_json()["available_copies"] == 0

'''
Function: list_reservations
'''

def test_list_reservations_returns_empty_list_when_none_exist(client):
	response = client.get("/reservations")

	assert response.status_code == 200
	assert response.get_json() == []


def test_list_reservations_returns_all_and_filters_by_book_or_member(client):
	member_response = client.post(
		"/members",
		json={"name": "Alice", "email": "alice3@gmail.com"}
	)

	other_member_response = client.post(
		"/members",
		json={"name": "Bob", "email": "bob3@gmail.com"}
	)

	book_response = client.post(
		"/books",
		json={
			"title": "Test Book",
			"author": "Test Author",
			"isbn": "1234567890",
			"total_copies": 1
		}
	)

	other_book_response = client.post(
		"/books",
		json={
			"title": "Other Book",
			"author": "Other Author",
			"isbn": "0987654321",
			"total_copies": 1
		}
	)
	member_id = member_response.get_json()["id"]
	other_member_id = other_member_response.get_json()["id"]
	book_id = book_response.get_json()["id"]
	other_book_id = other_book_response.get_json()["id"]

	client.post(
		"/reservations",
		json={"book_id": book_id, "member_id": member_id}
	)
	client.post(
		"/reservations",
		json={"book_id": other_book_id, "member_id": other_member_id}
	)

	all_reservations = client.get("/reservations")
	by_book = client.get(f"/reservations?book_id={book_id}")
	by_member = client.get(f"/reservations?member_id={other_member_id}")
	by_both = client.get(
		f"/reservations?book_id={book_id}&member_id={member_id}"
	)

	assert all_reservations.status_code == 200
	assert len(all_reservations.get_json()) == 2
	
	assert len(by_book.get_json()) == 1
	assert by_book.get_json()[0]["book_id"] == book_id

	assert len(by_member.get_json()) == 1
	assert by_member.get_json()[0]["member_id"] == other_member_id

	assert len(by_both.get_json()) == 1
	assert by_both.get_json()[0]["book_id"] == book_id
	assert by_both.get_json()[0]["member_id"] == member_id


def test_list_reservations_returns_empty_list_for_unmatched_filters(client):
	response = client.get("/reservations?book_id=999&member_id=999")

	assert response.status_code == 200
	assert response.get_json() == []

'''
Function: get_fine
'''

def test_get_fine_returns_zero_on_due_date(client):
	book = client.post(
		"/books",
		json={
			"title": "Test Book",
			"author": "Test Author",
			"isbn": "1234567890",
			"total_copies": 1
		}
	).get_json()

	loan = client.post(
		"/loans",
		json={"book_id": book["id"], "member_id": 1}
	).get_json()

	store.loans[loan["id"]].due_date = date.today()

	response = client.get(f"/loans/{loan['id']}/fine")

	assert response.status_code == 200
	assert response.get_json() == {"loan_id": loan["id"], "fine_amount": 0}


def test_get_fine_calculates_overdue_amount(client):
	book = client.post(
		"/books",
		json={
			"title": "Test Book",
			"author": "Test Author",
			"isbn": "1234567890",
			"total_copies": 1
		}
	).get_json()

	loan = client.post(
		"/loans",
		json={"book_id": book["id"], "member_id": 1}
	).get_json()
	store.loans[loan["id"]].due_date = date.today() - timedelta(days=4)

	response = client.get(f"/loans/{loan['id']}/fine")

	assert response.status_code == 200
	assert response.get_json() == {"loan_id": loan["id"], "fine_amount": 1.0}


def test_get_fine_returns_error_for_missing_loan(client):
	response = client.get("/loans/999/fine")

	assert response.status_code == 404
	assert response.get_json() == {"error": "Loan not found"}

'''
Function: renew_loan
'''

def test_renew_loan_extends_due_date_by_loan_period(client):
	book = client.post(
		"/books",
		json={
			"title": "Test Book",
			"author": "Test Author",
			"isbn": "1234567890",
			"total_copies": 1
		}
	).get_json()
	loan = client.post(
		"/loans",
		json={"book_id": book["id"], "member_id": 1}
	).get_json()
	original_due_date = date.fromisoformat(loan["due_date"])

	response = client.put(f"/loans/{loan['id']}/renew")

	assert response.status_code == 200
	assert response.get_json()["due_date"] == (
		original_due_date + timedelta(days=14)
	).isoformat()


def test_renew_loan_on_due_date_extends_due_date_by_loan_period(client):
	book = client.post(
		"/books",
		json={
			"title": "Test Book",
			"author": "Test Author",
			"isbn": "1234567890",
			"total_copies": 1
		}
	).get_json()

	loan = client.post(
		"/loans",
		json={"book_id": book["id"], "member_id": 1}
	).get_json()

	store.loans[loan["id"]].due_date = date.today()

	response = client.put(f"/loans/{loan['id']}/renew")

	assert response.status_code == 200
	assert response.get_json()["due_date"] == (
		date.today() + timedelta(days=14)
	).isoformat()


def test_renew_loan_returns_error_for_missing_loan(client):
	response = client.put("/loans/999/renew")

	assert response.status_code == 404
	assert response.get_json() == {"error": "Loan not found"}


def test_renew_loan_returns_error_for_already_returned_loan(client):
	book = client.post(
		"/books",
		json={
			"title": "Test Book",
			"author": "Test Author",
			"isbn": "1234567890",
			"total_copies": 1
		}
	).get_json()

	loan = client.post(
		"/loans",
		json={"book_id": book["id"], "member_id": 1}
	).get_json()
	
	client.put(f"/loans/{loan['id']}/return")

	response = client.put(f"/loans/{loan['id']}/renew")

	assert response.status_code == 400
	assert response.get_json() == {"error": "Loan already returned"}

'''
Function: list_loans
'''

'''
Function: Reservation.to_dict
'''

'''
Function: Reservation._init_
'''