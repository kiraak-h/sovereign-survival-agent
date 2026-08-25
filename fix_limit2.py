import sys
with open('core/limit_engine.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace("def __init__(self):", "def __init__(self, metabolism=None):")
content = content.replace("self.metabolism = MetabolismManager()", "self.metabolism = metabolism")

with open('core/limit_engine.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated LimitEngine init")
