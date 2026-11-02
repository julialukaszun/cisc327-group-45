# test_julia.py

def test_delete_book_successfully(client):
    
    payload = {"title": "Clean Code",
                        "author": "Robert C. Martin",
                        "isbn": "978-0132350884",
                        "total_copies": 2,}
    
    
    post_response = client.post("/books", json=payload)
    
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
    
    
    
    
    
    
        