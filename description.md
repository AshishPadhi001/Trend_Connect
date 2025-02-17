# Trend Connect API Documentation

This repository contains a REST API for Trend Connect, a platform focused on connecting people and content.

## Authentication Routes:

* **GET** `/Login_welcome`: Welcome message for login page.
* **POST** `/login`: Authenticate a user.
* **POST** `/logout`: Logout a user.

## User Routes:

* **GET** `/`: Welcome message for the API. 
* **POST** `/send_otp`: Send a One-Time Password (OTP) to a user via email or phone for verification.
* **POST** `/verify_otp`: Verify a user's OTP.
* **POST** `/register`: Register a new user (requires photo, password, date of birth, phone number, email, and country).
* **GET** `/get_users`: Retrieve a list of all users.
* **GET** `/get_user/{id}`: Retrieve user information by ID.
* **DELETE** `/delete_user/{id}`: Delete a user by ID.
* **PUT** `/update_user/{id}`: Update a user's password by ID.

## Content Routes:

* **GET** `/welcome`: Welcome message for the content page.
* **POST** `/create_content`: Create new content, supporting file uploads.
* **GET** `/get_content`: Retrieve a list of all content.
* **GET** `/get_content/{id}`: Retrieve content by ID.
* **DELETE** `/delete_content/{id}`: Delete content by ID.
* **PUT** `/update_content/{id}`: Update existing content by ID.

## Likes Routes:

* **POST** `/likes`: Manage likes on posts (requires `user_id`, `username`, and `post_id`).

## Comment Routes:

* **POST** `/comments`: Manage comments on posts (requires `user_id`, `username`, and `post_id`).

## Search Routes:

* **GET** `/search`: Search for users by username with pagination. Returns similar usernames in ascending order. Default: Page 1, 6 users per page.
* **GET** `/search_by_title`: Search content by title or content ID with pagination. Returns similar titles in ascending order. Default: Page 1, 6 contents per page.

## Profile Routes:

* **POST** `/user_profile`: Authenticate the user using username and password, then return the user's profile, content, follower count, and following count.
* **GET** `/followers/{username}`: Retrieve a list of users who follow a specified user, including the date they started following.
* **GET** `/following/{username}`: Retrieve a list of users that a specified user is following, including the date they started following.

## Follow Routes:

* **POST** `/follow`: Follow a user (requires `user_id`). You cannot follow yourself.
* **DELETE** `/unfollow`: Unfollow a user (requires `user_id`).

**Note:** This documentation is a basic outline. Ensure to refer to the codebase and API specifications for detailed information and potential endpoints.



