import os
from alice_blue import AliceBlue

def login():
    user_id = os.getenv("ALICE_USER_ID")
    password = os.getenv("ALICE_PASSWORD")
    two_fa = os.getenv("ALICE_TWO_FA")
    app_id = os.getenv("ALICE_APP_ID")
    api_secret = os.getenv("ALICE_API_SECRET")

    print(f"DEBUG: Logging in with user_id={user_id}, app_id={app_id}")

    session_id = AliceBlue.login_and_get_sessionID(
        username=user_id,
        password=password,
        twoFA=two_fa,
        app_id=app_id,
        api_secret=api_secret
    )

    alice = AliceBlue(user_id=user_id, session_id=session_id)
    print("✅ Successfully logged into Alice Blue")
    return alice
