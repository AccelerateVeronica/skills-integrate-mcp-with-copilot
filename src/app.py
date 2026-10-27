"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

from fastapi import FastAPI, HTTPException
from fastapi import Depends, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
import hashlib
import hmac
import os
from pathlib import Path
import time

app = FastAPI(title="Mergington High School API",
              description="API for viewing extracurricular activities and managing registrations")

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")

# In-memory activity database
activities = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"]
    },
    "Soccer Team": {
        "description": "Join the school soccer team and compete in matches",
        "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
        "max_participants": 22,
        "participants": ["liam@mergington.edu", "noah@mergington.edu"]
    },
    "Basketball Team": {
        "description": "Practice and play basketball with the school team",
        "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["ava@mergington.edu", "mia@mergington.edu"]
    },
    "Art Club": {
        "description": "Explore your creativity through painting and drawing",
        "schedule": "Thursdays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["amelia@mergington.edu", "harper@mergington.edu"]
    },
    "Drama Club": {
        "description": "Act, direct, and produce plays and performances",
        "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
        "max_participants": 20,
        "participants": ["ella@mergington.edu", "scarlett@mergington.edu"]
    },
    "Math Club": {
        "description": "Solve challenging problems and participate in math competitions",
        "schedule": "Tuesdays, 3:30 PM - 4:30 PM",
        "max_participants": 10,
        "participants": ["james@mergington.edu", "benjamin@mergington.edu"]
    },
    "Debate Team": {
        "description": "Develop public speaking and argumentation skills",
        "schedule": "Fridays, 4:00 PM - 5:30 PM",
        "max_participants": 12,
        "participants": ["charlotte@mergington.edu", "henry@mergington.edu"]
    }
}

SESSION_COOKIE = "teacher_session"
SESSION_MAX_AGE = 8 * 60 * 60


class TeacherLogin(BaseModel):
    username: str
    password: str


def get_teacher_credentials():
    username = os.environ.get("TEACHER_USERNAME")
    password = os.environ.get("TEACHER_PASSWORD")
    secret = os.environ.get("SESSION_SECRET")

    if not username or not password or not secret or len(secret) < 32:
        raise HTTPException(
            status_code=503,
            detail="Teacher login is not configured. Set TEACHER_USERNAME, "
                   "TEACHER_PASSWORD, and a SESSION_SECRET of at least 32 characters.",
        )

    return username, password, secret


def make_session_signature(timestamp: str, secret: str) -> str:
    return hmac.new(
        secret.encode("utf-8"),
        timestamp.encode("ascii"),
        hashlib.sha256,
    ).hexdigest()


def is_teacher_authenticated(request: Request) -> bool:
    username, _, secret = get_teacher_credentials()
    session = request.cookies.get(SESSION_COOKIE, "")

    try:
        timestamp, signature = session.split(".", maxsplit=1)
        if not timestamp.isascii() or not timestamp.isdigit() or not signature.isascii():
            return False
        issued_at = int(timestamp)
    except ValueError:
        return False

    expected_signature = make_session_signature(timestamp, secret)
    return (
        hmac.compare_digest(signature, expected_signature)
        and 0 <= time.time() - issued_at <= SESSION_MAX_AGE
        and bool(username)
    )


def require_teacher(request: Request):
    if not is_teacher_authenticated(request):
        raise HTTPException(status_code=401, detail="Teacher login required")


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.post("/auth/login")
def login(credentials: TeacherLogin, request: Request, response: Response):
    username, password, secret = get_teacher_credentials()
    if not (
        hmac.compare_digest(credentials.username.encode("utf-8"), username.encode("utf-8"))
        and hmac.compare_digest(credentials.password.encode("utf-8"), password.encode("utf-8"))
    ):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    timestamp = str(int(time.time()))
    signature = make_session_signature(timestamp, secret)
    response.set_cookie(
        key=SESSION_COOKIE,
        value=f"{timestamp}.{signature}",
        max_age=SESSION_MAX_AGE,
        httponly=True,
        secure=request.url.scheme == "https",
        samesite="strict",
        path="/",
    )
    return {"authenticated": True}


@app.get("/auth/me")
def get_authentication_status(request: Request):
    return {"authenticated": is_teacher_authenticated(request)}


@app.post("/auth/logout")
def logout(request: Request, response: Response):
    response.delete_cookie(
        key=SESSION_COOKIE,
        httponly=True,
        secure=request.url.scheme == "https",
        samesite="strict",
        path="/",
    )
    return {"authenticated": False}


@app.get("/activities")
def get_activities():
    return activities


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(activity_name: str, email: str, _: None = Depends(require_teacher)):
    """Sign up a student for an activity"""
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is not already signed up
    if email in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is already signed up"
        )

    # Add student
    activity["participants"].append(email)
    return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(activity_name: str, email: str, _: None = Depends(require_teacher)):
    """Unregister a student from an activity"""
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is signed up
    if email not in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is not signed up for this activity"
        )

    # Remove student
    activity["participants"].remove(email)
    return {"message": f"Unregistered {email} from {activity_name}"}
