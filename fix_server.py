import sys
with open('server.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace("_limit_engine = LimitEngine()", "_limit_engine = LimitEngine(metabolism=_metabolism)")

with open('server.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated server.py limit engine init")
