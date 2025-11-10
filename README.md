# COMP4651 Chatroom Microservice as a Containerized Application

This repository contains a simple chatroom microservice implemented as a containerized application and deployed using Kubernetes.

## Authentication Microservice
Issues JWT via /login POST request

### Endpoints 
|Method | Endpoint     | Description                  |
|-------|--------------|------------------------------|
| POST  | /login       | Authenticate user            |
| PUST  | /generate_db | Generate testing users in db |

### /login
Submit JSON in body like this  
{
    "username": "John",
    "password": "Doe
}  
Return example:  
{
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOjEsImV4cCI6MTc2Mjc5NDA5Mn0.VvLxT72zrL8PKQb0RnW6kxD09XwjG-zGXeaF8y9mJuo"
}
### /generate_db
Generates the following dummy users in db with (username,password):  
("alice", "pass123"),  
("bob", "qwerty"),  
("charlie", "hello123"),  
("dave", "abc123"),  
("emma", "secret1"),  
("frank", "test123"),  
("grace", "password1"),  
("henry", "letmein"),  
("isabella", "monkey1"),  
("jack", "simple123")  