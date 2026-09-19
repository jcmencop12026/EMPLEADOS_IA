import os
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(r"D:\EMPLEADOS_IA\backend")))

from app.gateway.gmail_oauth import refresh_access_token, smtp_xoauth2_login
from app.services import communications_service as svc

smtp = Mock()
smtp.docmd.return_value = (235, b"2.7.0 Accepted")
smtp_xoauth2_login(smtp, username="user@gmail.com", access_token="token-demo")
assert smtp.docmd.call_args.args[0] == "AUTH"
assert smtp.docmd.call_args.args[1].startswith("XOAUTH2 ")
print("PASS xoauth2 AUTH 235")

smtp_bad = Mock()
smtp_bad.docmd.return_value = (535, b"Rejected")
try:
    smtp_xoauth2_login(smtp_bad, username="user@gmail.com", access_token="bad")
    raise AssertionError("debio fallar")
except Exception as exc:
    assert exc.__class__.__name__ == "SMTPAuthenticationError"
print("PASS xoauth2 AUTH 535")

response = Mock()
response.raise_for_status.return_value = None
response.json.return_value = {"access_token": "abc123"}
with patch("app.gateway.gmail_oauth.httpx.post", return_value=response) as post:
    token = refresh_access_token(client_id="cid", client_secret="sec", refresh_token="rt")
    assert token == "abc123"
    assert post.call_args.kwargs["data"]["grant_type"] == "refresh_token"
print("PASS refresh token")

os.environ["QA_SMTP_PASSWORD"] = "demo-password"
channel = SimpleNamespace(secret_ref="env:QA_SMTP_PASSWORD")
smtp_pw = Mock()
svc._smtp_authenticate(smtp_pw, channel, {"auth_mode": "password"}, "u@example.com")
smtp_pw.login.assert_called_once_with("u@example.com", "demo-password")
print("PASS password fallback")

os.environ["EIIAX_GMAIL_OAUTH_CLIENT_ID"] = "cid"
os.environ["EIIAX_GMAIL_OAUTH_CLIENT_SECRET"] = "csecret"
os.environ["EIIAX_GMAIL_OAUTH_REFRESH_TOKEN"] = "rt"
smtp_oauth = Mock()
with patch.object(svc, "refresh_access_token", return_value="access") as refresh, patch.object(svc, "smtp_xoauth2_login") as login:
    svc._smtp_authenticate(smtp_oauth, channel, {"auth_mode": "oauth2"}, "u@gmail.com")
    refresh.assert_called_once_with(client_id="cid", client_secret="csecret", refresh_token="rt")
    login.assert_called_once_with(smtp_oauth, username="u@gmail.com", access_token="access")
print("PASS oauth2 service branch")
print("QA_GMAIL_OAUTH_OK")
