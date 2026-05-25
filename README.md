---
title: AI Keystroke Security System
emoji: 🔐
colorFrom: blue
colorTo: purple
sdk: docker
pinned: false
---

# AI-Based Secure Authentication System Using Keystroke Dynamics

This is a BTech mini project that authenticates a user by typing behavior. It includes a desktop GUI, machine learning model training, multiple user profiles, an admin dashboard, graphs, and a Flask web version for deployment on GitHub and Hugging Face.

## Main idea

Instead of checking only the password text, this project also checks how the user types. It uses keystroke dynamics such as hold time, flight time, and engineered typing features to identify genuine users and reject impostors.

## Core concepts

### Keystroke Dynamics
Keystroke dynamics means identifying a person by typing pattern.

### Hold Time
Hold time is the time between pressing and releasing the same key.

### Flight Time
Flight time is the time gap between one key and the next key.

### Authentication
Authentication means deciding whether the current user is the real authorized user.

## Modules

1. Keystroke Data Capture
2. Dataset Creation
3. Machine Learning Model Training
4. User Registration and Profile Creation
5. User Authentication
6. Admin Dashboard
7. Accuracy Evaluation
8. GUI Login System
9. Web Deployment Version

## Folder structure

```text
MINOR P/
|-- capture_data.py
|-- train_model.py
|-- register_user.py
|-- authenticate.py
|-- login_gui.py
|-- accuracy_graph.py
|-- backend_utils.py
|-- admin_dashboard.py
|-- profile_compare.py
|-- web_app.py
|-- app.py
|-- Dockerfile
|-- requirements.txt
|-- README.md
|-- .gitignore
|-- data/
|   |-- genuine.csv
|   |-- impostor.csv
|   |-- auth_log.csv
|   |-- security_system.db
|   `-- user_profiles/
`-- models/
    |-- model.pkl
    |-- metrics.json
    `-- user_profiles/
```

## File explanation

### capture_data.py
Captures keystroke hold times and stores them in `genuine.csv` or `impostor.csv`.

### train_model.py
Loads data, creates features, compares models like Random Forest, Extra Trees, and SVM, then saves the best model.

### register_user.py
Registers a named user and creates that user's typing profile.

### authenticate.py
Runs a simple authentication test outside the main GUI.

### login_gui.py
Main desktop application with animations, voice alerts, login logic, and user profile selection.

### accuracy_graph.py
Shows model performance graphs and comparison charts.

### backend_utils.py
Project backend logic for feature engineering, prediction, SQLite storage, settings, logs, and profile comparison.

### admin_dashboard.py
Admin dashboard showing total users, total attempts, granted and denied attempts, export option, and settings.

### profile_compare.py
Compares a fresh typing sample with a selected saved user profile.

### web_app.py
Flask web app version used for browser deployment.

### app.py
Deployment entry point for Hugging Face Spaces.

## Local setup

### 1. Open the project folder

```bash
cd "C:\Users\DELL\OneDrive\Desktop\MINOR P"
```

### 2. Install required libraries

```bash
pip install -r requirements.txt
```

### 3. Capture dataset

```bash
python capture_data.py
```

Choose:
- `1` for genuine samples
- `2` for impostor samples

### 4. Train the model

```bash
python train_model.py
```

This creates:
- `models/model.pkl`
- `models/metrics.json`

### 5. Register users

```bash
python register_user.py
```

### 6. Run desktop GUI

```bash
python login_gui.py
```

### 7. Run admin dashboard

```bash
python admin_dashboard.py
```

### 8. Show graphs

```bash
python accuracy_graph.py
```

### 9. Run web version locally

```bash
python app.py
```

Then open:

```text
http://127.0.0.1:7860
```

## Expected outputs

### Training output
- best model name
- accuracy
- cross-validation results
- saved model and metrics

### Desktop GUI output
- animated login screen
- access granted or denied
- voice and alert effects
- live status and confidence

### Admin output
- total users
- total login attempts
- granted and denied counts
- exported history

### Graph output
- accuracy
- precision
- recall
- F1-score
- model comparison
- user sample counts

### Web output
- browser-based login page
- admin page at `/admin`

## GitHub upload

### Step 1

```bash
git init
git add .
git commit -m "Initial commit"
```

### Step 2
Create a new repository on GitHub, then run:

```bash
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPOSITORY_NAME.git
git push -u origin main
```

## Hugging Face deployment

Tkinter desktop GUI cannot run directly on Hugging Face Spaces. Use the Flask web version instead.

### Step 1
Create a new Hugging Face Space and choose:
- `Docker`

### Step 2
Upload these important files:
- `app.py`
- `web_app.py`
- `backend_utils.py`
- `requirements.txt`
- `Dockerfile`

### Step 3
If you want live authentication to work immediately, also upload:
- `models/model.pkl`
- `models/metrics.json`
- `models/user_profiles/`
- any required demo data in `data/`

### Step 4
Hugging Face will build the Space automatically and run it on port `7860`.

## Best demo commands

### Desktop demo

```bash
python train_model.py
python register_user.py
python login_gui.py
python accuracy_graph.py
```

### Web demo

```bash
python app.py
```

## 1-minute explanation

This project is an AI-based secure authentication system using keystroke dynamics. It checks not only the typed text, but also the user's typing behavior. First, typing samples are collected from genuine and impostor users. Then machine learning models are trained on features like hold time and flight time. Each user can also register a personal typing profile. During login, the current typing pattern is compared with both the trained model and the stored user profile. If the pattern matches, access is granted; otherwise, access is denied. The project also includes an animated desktop GUI, graphs, admin tools, and a web deployment version.

## Real-life applications

1. Banking login security
2. Office system login
3. Online examination verification
4. Secure lab or research access
5. Background user verification in web apps

## Viva questions

### 1. What is keystroke dynamics?
It is a behavioral biometric method that identifies users from typing patterns.

### 2. What is hold time?
It is the time between key press and key release.

### 3. Why is machine learning used?
It learns the typing pattern of genuine and impostor users and helps classify new samples.

### 4. Which models are used?
Random Forest, Extra Trees, and SVM.

### 5. Why is this project useful?
It improves security beyond normal password-only systems without extra hardware.
