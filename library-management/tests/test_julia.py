# test_julia.py

# tests for deleting a book

def test_delete_book_successfully(client):
    
    payload = {"title": "Clean Code",
                        "author": "Robert C. Martin",
                        "isbn": "978-0132350884",
                        "total_copies": 2,}
    
    
    client.post("/books", json=payload)
    
    delete_response = client.delete("/books/1")
    
    assert delete_response.status_code == 204
    assert delete_response.text == ''
    
def test_delete_non_existing_book(client):
    response = client.delete("/books/999")
    
    assert response.status_code == 404
    assert response.json == {"error": "Book not found"}
    
def test_delete_book_invalid_id_type(client):
    response = client.delete("/books/abc")
    
    assert response.status_code == 404
    
# tests for returning a loaned book

def test_return_loaned_book_successfully(client):
    
    book_payload = {"title": "Clean Code",
                        "author": "Robert C. Martin",
                        "isbn": "978-0132350884",
                        "total_copies": 2,}
    
    client.post("/books", json=book_payload)
    
    loan_payload = {
        "book_id": 1,
        "member_id": 1
    }
    
    client.post("/loans", json=loan_payload)
    
    response = client.put("/loans/1/return")
    
    assert response.status_code == 200
    assert response.json["return_date"] is not None
    
    book_response = client.get("/books/1")
    assert book_response.json["available_copies"] == 2
    
def test_return_book_already_returned(client):
    book_payload = {"title": "Clean Code",
                            "author": "Robert C. Martin",
                            "isbn": "978-0132350884",
                            "total_copies": 2,}
        
    client.post("/books", json=book_payload)
        
    loan_payload = {
            "book_id": 1,
            "member_id": 1
        }
        
    client.post("/loans", json=loan_payload)
        
    response_1 = client.put("/loans/1/return")
    assert response_1.status_code == 200
    
    response_2 = client.put("/loans/1/return")
    
    assert response_2.status_code == 400
    assert response_2.json == {"error": "Loan already returned"}
    
def test_return_book_loan_not_found(client):
    
    response = client.put("/loans/999/return")
    
    assert response.status_code == 404
    assert response.json == {"error": "Loan not found"}

def test_return_book_invalid_id_type(client):
    
    response = client.put("/loans/abc/return")
    
    assert response.status_code == 404

# tests for adding a book (other than example test)

def test_create_book_with_default_copies(client):
    payload = {"title": "Clean Code",
                            "author": "Robert C. Martin",
                            "isbn": "978-0132350884"}
    
    response = client.post("/books", json=payload)
    
    assert response.status_code == 201
    assert response.json["total_copies"] == 1
    assert response.json["available_copies"] == 1
    
def test_search_books_by_title(client):
    payload_1 = {"title": "Clean Code",
                        "author": "Robert C. Martin",
                        "isbn": "978-0132350884",
                        "total_copies": 2,}
    client.post("/books", json=payload_1)
    
    payload_2 = {"title": "Scrabbled Code",
                        "author": "Hubert C. Martin",
                        "isbn": "978-0132350888",
                        "total_copies": 1,}
    client.post("/books", json=payload_2)
        

    response = client.get("/books?search=Scrabbled Code")

    assert response.status_code == 200
    assert len(response.get_json()) == 1
    assert response.get_json()[0]["title"] == "Scrabbled Code"


def test_search_books_by_isbn(client):
    payload = {"title": "Clean Code",
                        "author": "Robert C. Martin",
                        "isbn": "978-0132350884",
                        "total_copies": 2,}
    client.post("/books", json=payload)

    response = client.get("/books?search=978-0132350884")

    assert response.status_code == 200
    assert len(response.get_json()) == 1
    assert response.get_json()[0]["title"] == "Clean Code"
    
    
    
    
    
        