from unittest.mock import patch


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