from datetime import datetime

import lorem
import requests
import json
import random

# Load configuration
with open('config.json', 'r') as config_file:
    config = json.load(config_file)

API_BASE_URL = 'http://127.0.0.1:5000/api'

# Headers for sending JSON requests
headers = {'Content-Type': 'application/json'}


def get_unique_email(user_index):
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    return f"user{user_index}-{timestamp}@example.com"


def generate_random_content(number_of_sentences=2):
    sentences = [lorem.sentence() for _ in range(number_of_sentences)]
    return ' '.join(sentences)


def signup_user(email, password):
    response = requests.post(
        f"{API_BASE_URL}/signup",
        json={"email": email, "password": password},
        headers=headers
    )
    print(
        f"Signup status for {email}: {response.status_code}, Response: {response.text}")
    if response.status_code == 201:
        return response.json()
    else:
        print(
            f"Failed to sign up {email}. Status code: {response.status_code}, Response message: {response.text}")
    return None


def login_user(email, password):
    response = requests.post(
        f"{API_BASE_URL}/login",
        json={"email": email, "password": password},
        headers=headers
    )
    print(f"Login status for {email}: {response.status_code}")
    if response.status_code == 200:
        return response.json()['access_token']
    return None


def create_post(user_token, content):
    response = requests.post(
        f"{API_BASE_URL}/post",
        json={"content": content},
        headers={'Authorization': f'Bearer {user_token}'}
    )
    print(f"Create post status: {response.status_code}")
    if response.status_code == 201:
        return response.json()['post_id']
    return None


def like_post(user_token, post_id):
    response = requests.post(
        f"{API_BASE_URL}/post/{post_id}/like",
        headers={'Authorization': f'Bearer {user_token}'}
    )
    if response.status_code == 200:
        print(
            f"Like post status: {response.status_code}, Post ID: {post_id} - Success")
        return True
    elif response.status_code == 409:
        print(
            f"Like post status: {response.status_code}, Post ID: {post_id} - Already liked (as expected)")
        return False
    else:
        print(
            f"Like post status: {response.status_code}, Post ID: {post_id} - Error")
        return False


def perform_bot_activities():
    users = []
    posts = []

    # Sign up users
    for i in range(config['number_of_users']):
        unique_email = get_unique_email(i)
        password = 'password'
        signup_result = signup_user(unique_email, password)
        if signup_result:
            users.append({'email': unique_email,
                          'password': password,
                          'token': signup_result['access_token']})

    # Log in users and create posts
    for user in users:
        token = login_user(user['email'], user['password'])
        if token:
            for _ in range(random.randint(1, config['max_posts_per_user'])):
                post_content = generate_random_content()
                post_id = create_post(token, post_content)
                if post_id:
                    posts.append(post_id)

    # Like posts randomly
    for user in users:
        token = login_user(user['email'], user['password'])
        if token:
            liked_posts = 0
            while liked_posts < config['max_likes_per_user'] and posts:
                post_to_like = random.choice(posts)
                if like_post(token, post_to_like):
                    liked_posts += 1
                else:
                    posts.remove(post_to_like)


if __name__ == '__main__':
    perform_bot_activities()
