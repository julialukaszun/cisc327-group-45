'''
Reponsibilities include:

Adding a member
	Testing Procedure:
		Expected input
		Unexpected input:
			Empty name
			Empty email
			Incorrect email formatting
			Email characters too long
			
		
	
Deleting a member
	Testing procedure:
		Create a member then delete it
		Make sure "" is returned
		Delete non-existing member

Checking out a book
	Testing procedure:
		Check if loan is created
		Check if book available copies decrements

'''
import pytest

'''
Function: Creating a member
'''

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


def test_create_member_with_empty_name_returns_error(client):
	payload = {
		"name": None,
		"email": "alice3@gmail.com"
	}

	response = client.post("/members", json=payload)

	assert response.status_code == 400
	assert response.get_json() == {"error": "Name is required"}


def test_create_member_with_empty_email_returns_error(client):
	payload = {
		"name": "Alice",
		"email": ""
	}

	response = client.post("/members", json=payload)

	assert response.status_code == 400
	assert response.get_json() == {"error": "Email is required"}

def test_create_member_with_invalid_email_returns_error(client): # Checks API
	payload = {
		"name": "Alice",
		"email": "not-an-email"
	}

	response = client.post("/members", json=payload)

	assert response.status_code == 400
	assert response.get_json() == {"error": "Invalid email"}

def test_members_form_requires_valid_email_format(client): # Checks website form
	response = client.get("/ui/members")

	assert response.status_code == 200
	assert b'<input type="email" name="email" required>' in response.data



'''
Function: Deleting a member
'''

def test_delete_member_returns_empty(client):
	payload = {
		"name": "Alice", 
		"email": "alice3@gmail.com"
		}
	created = client.post("/members", json=payload)
	member_id = created.get_json()["id"]


	response = client.delete(f"members/{member_id}")
	assert response.status_code == 204
	assert response.get_data(as_text=True) == ""


def test_delete_member_removes_member(client):
	created = client.post(
		"/members",
		json={"name": "Alice", "email": "alice3@gmail.com"}
	)
	member_id = created.get_json()["id"]

	response = client.delete(f"/members/{member_id}")

	assert response.status_code == 204
	assert client.get(f"/members/{member_id}").status_code == 404


def test_delete_nonexistent_member_returns_error(client):
	response = client.delete("/members/999")

	assert response.status_code == 404
	assert response.get_json() == {"error": "Member not found"}

'''
Function: Checking out a book
'''

def test_checkout_book_creates_loan(client):
	member_response = client.post(
		"/members",
		json={
			"name": "Alice", 
			"email": "alice3@gmail.com"
		}
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
	
	member_id = member_response.get_json()["id"]
	book_id = book_response.get_json()["id"]

	response = client.post(
		"/loans",
		json={"book_id": book_id, "member_id": member_id}
	)

	assert response.status_code == 201
	loan = response.get_json()
	assert loan["id"] == 1
	assert loan["book_id"] == book_id
	assert loan["member_id"] == member_id
	assert loan["loan_date"]
	assert loan["due_date"]
	assert loan["return_date"] is None

	updated_book = client.get(f"/books/{book_id}").get_json()
	assert updated_book["available_copies"] == 0


def test_checkout_nonexistent_book_returns_error(client):
	response = client.post(
		"/loans",
		json={"book_id": 999, "member_id": 1}
	)

	assert response.status_code == 404
	assert response.get_json() == {"error": "Book not found"}


def test_return_book_restores_available_copy(client):
	book_response = client.post(
		"/books",
		json={
			"title": "Test Book",
			"author": "Test Author",
			"isbn": "1234567890",
			"total_copies": 1
		}
	)

	book_id = book_response.get_json()["id"]
	loan_response = client.post(
		"/loans",
		json={"book_id": book_id, "member_id": 1}
	)

	loan_id = loan_response.get_json()["id"]

	response = client.put(f"/loans/{loan_id}/return")

	assert response.status_code == 200
	assert response.get_json()["return_date"]
	updated_book = client.get(f"/books/{book_id}").get_json()
	assert updated_book["available_copies"] == 1


def test_return_nonexistent_loan_returns_error(client):
	response = client.put("/loans/999/return")

	assert response.status_code == 404
	assert response.get_json() == {"error": "Loan not found"}


def test_return_already_returned_loan_returns_error(client):
	book_response = client.post(
		"/books",
		json={
			"title": "Test Book",
			"author": "Test Author",
			"isbn": "1234567890",
			"total_copies": 1
		}
	)
	book_id = book_response.get_json()["id"]
	loan_response = client.post(
		"/loans",
		json={"book_id": book_id, "member_id": 1}
	)

	loan_id = loan_response.get_json()["id"]
	client.put(f"/loans/{loan_id}/return")

	response = client.put(f"/loans/{loan_id}/return")

	assert response.status_code == 400
	assert response.get_json() == {"error": "Loan already returned"}
