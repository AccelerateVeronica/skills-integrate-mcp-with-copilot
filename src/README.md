# Mergington High School Activities API

A simple FastAPI application that lets visitors view extracurricular activities and lets teachers manage student registrations.

## Features

- View all available extracurricular activities
- Teachers can register and unregister students after logging in
- Students and visitors can view activities and current registrations

## Getting Started

1. Install the dependencies:

   ```
   pip install -r requirements.txt
   ```

2. Configure the teacher login in the environment. Do not put credentials in the repository:

   ```
   export TEACHER_USERNAME="teacher"
   export TEACHER_PASSWORD="use-a-unique-strong-password"
   export SESSION_SECRET="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
   ```

   Keep the same `SESSION_SECRET` across application restarts to preserve active sessions. Teacher login remains unavailable until all three variables are set and the session secret contains at least 32 characters.

3. Run the application:

   ```
   uvicorn app:app --reload --app-dir src
   ```

4. Open your browser and go to:
   - API documentation: http://localhost:8000/docs
   - Alternative documentation: http://localhost:8000/redoc

## API Endpoints

| Method | Endpoint                                                          | Description                                                           |
| ------ | ----------------------------------------------------------------- | --------------------------------------------------------------------- |
| GET    | `/activities`                                                     | Get all activities and current registrations                          |
| POST   | `/auth/login`                                                      | Log in as a teacher; sets an HTTP-only session cookie                  |
| GET    | `/auth/me`                                                         | Check whether the current browser has an active teacher session       |
| POST   | `/auth/logout`                                                     | End the current teacher session                                        |
| POST   | `/activities/{activity_name}/signup?email=student@mergington.edu` | Register a student (teacher login required)                            |
| DELETE | `/activities/{activity_name}/unregister?email=student@mergington.edu` | Unregister a student (teacher login required)                      |

## Data Model

The application uses a simple data model with meaningful identifiers:

1. **Activities** - Uses activity name as identifier:

   - Description
   - Schedule
   - Maximum number of participants allowed
   - List of student emails who are signed up

2. **Students** - Uses email as identifier:
   - Name
   - Grade level

Activity and registration data is stored in memory, which means it will be reset when the server restarts. Teacher sessions are signed, expire after eight hours, and use an HTTP-only, SameSite cookie.
