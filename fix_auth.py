'
with open("server.py", "r", encoding="utf-8") as f:
    content = f.read()

auth_block = """security = HTTPBasic()
def get_current_username(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, "admin")
    correct_password = secrets.compare_digest(credentials.password, "sovereign2026")
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username"""

content = content.replace(auth_block, "")
content = content.replace("import secrets", "import secrets\\n\\n" + auth_block + "\\n\\n")

with open("server.py", "w", encoding="utf-8") as f:
    f.write(content)
print("Done")
'
