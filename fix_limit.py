import sys
with open('core/limit_engine.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace("from core.notifier import SovereignNotifier", "from core.notifier import AgentNotifier")
content = content.replace("self.notifier = SovereignNotifier()", "self.notifier = AgentNotifier()")

with open('core/limit_engine.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Fixed LimitEngine Notifier Import")
