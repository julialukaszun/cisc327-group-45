import json

from app import create_app


'''
Checks that 
1. backup exists independently of the original app instance
2. creating a member and book automatically creates the backup file
3. checking out and returning 
4. test uses a temporary 
'''

def test_backup_is_created_and_updated_by_api(client, tmp_path):
    backup_path = tmp_path / "backup.json"
    client.application.config["BACKUP_FILE"] = str(backup_path)

    member_response = client.post(
        "/members",
        json={
            "name": "Alice", 
            "email": "alice6@gmail.com"
            },
    )
    book_response = client.post(
        "/books",
        json={
            "title": "Original Title",
            "author": "Test Author",
            "isbn": "1234567890",
            "total_copies": 2,
        },
    )
    member_id = member_response.get_json()["id"]
    book_id = book_response.get_json()["id"]

    assert backup_path.is_file()
    initial_backup = json.loads(backup_path.read_text(encoding="utf-8"))
    assert initial_backup["members"][0]["name"] == "Alice"
    assert initial_backup["books"][0]["title"] == "Original Title"

    client.put(f"/members/{member_id}", json={"name": "Alice Updated"})
    client.put(f"/books/{book_id}", json={"title": "Updated Title"})

    response = client.get("/backup")

    assert response.status_code == 200
    backup = response.get_json()
    assert backup["members"][0]["name"] == "Alice Updated"
    assert backup["books"][0]["title"] == "Updated Title"

    loan_response = client.post(
        "/loans",
        json={
            "book_id": book_id, 
            "member_id": member_id
        },
    )
    loan_id = loan_response.get_json()["id"]
    assert client.get("/backup").get_json()["books"][0]["available_copies"] == 1

    client.put(f"/loans/{loan_id}/return")
    assert client.get("/backup").get_json()["books"][0]["available_copies"] == 2

    client.delete(f"/members/{member_id}")
    client.delete(f"/books/{book_id}")
    backup = client.get("/backup").get_json()
    assert backup["members"] == []
    assert backup["books"] == []

    restarted_app = create_app()
    restarted_app.config["BACKUP_FILE"] = str(backup_path)
    with restarted_app.test_client() as restarted_client:
        persisted_response = restarted_client.get("/backup")

    assert persisted_response.status_code == 200
    assert persisted_response.get_json() == backup


def test_post_backup_creates_backup_when_no_data_changes(client, tmp_path):
    backup_path = tmp_path / "backup.json"
    client.application.config["BACKUP_FILE"] = str(backup_path)

    response = client.post("/backup")

    assert response.status_code == 200
    assert response.get_json()["books"] == []
    assert response.get_json()["members"] == []
    assert backup_path.is_file()
