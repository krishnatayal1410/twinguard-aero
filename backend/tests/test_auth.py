import secrets
from app.services.auth import signup,signin,session_user,signout

def test_auth_roundtrip():
 email=f"test-{secrets.token_hex(5)}@example.com"
 token,user=signup("Test Operator",email,"SecureTwin9A")
 assert user["email"]==email
 assert session_user(token)["name"]=="Test Operator"
 token2,user2=signin(email,"SecureTwin9A")
 assert user2["id"]==user["id"]
 signout(token2)
 assert session_user(token2) is None
