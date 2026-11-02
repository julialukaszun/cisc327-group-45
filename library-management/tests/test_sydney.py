'''
Reponsibilities include:

Adding a member
	Testing Procedure:
		Expected input
		Unexpected input:
			
		
	
Deleting a member
Returning a loaned book
'''
import pytest


def test_create_member_returns_created_member(client):
	payload = {
		"name": "Alice",
		"email": "alice3@gmail.com"
	}
	
	response = client.post(
		"/members",
		json=payload)

	assert response.status_code == 201
	data = response.get_json()
	assert data["name"] == "Alice"
	assert data["email"] == "alice3@gmail.com"



def test_delete_member_returns_empty(client):
	payload = {"name": "Alice", "email": "alice3@gmail.com"}
	created = client.post("/members", json=payload)
	member_id = created.get_json()["id"]


	response = client.delete(f"members/{member_id}")
	assert response.status_code == 204
	assert response.get_data(as_text=True) == ""


	