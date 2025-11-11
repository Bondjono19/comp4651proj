# COMP4651 Chatroom Microservice as a Containerized Application

This repository contains a simple chatroom microservice implemented as a containerized application and deployed using Kubernetes.

##  Quick Start

### Setup

```bash

cd backend

python -m venv venv

# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

pip install -r requirements.txt

python main.py

cd frontend

npm install

npm run dev
