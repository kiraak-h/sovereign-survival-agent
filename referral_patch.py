import re
with open('core/telegram_bot_service.py', 'r', encoding='utf-8') as f:
    c = f.read()
old_cmds = '''            commands = [
                {\
command\: \wallet\, \description\: \Generate
or
view
your
trading
wallet\},
                {\
command\: \status\, \description\: \View
live
agent
revenue
metrics\},
                {\
command\: \sweep\, \description\: \Force
on-chain
settlement\},
                {\
command\: \help\, \description\: \Show
help
and
command
guide\}
            ]'''
new_cmds = '''            commands = [
                {\
command\: \wallet\, \description\: \Generate
or
view
your
trading
wallet\},
                {\
command\: \refer\, \description\: \Get
your
referral
link
and
view
earnings\},
                {\
command\: \status\, \description\: \View
live
agent
revenue
metrics\},
                {\
command\: \sweep\, \description\: \Force
on-chain
settlement\},
                {\
command\: \help\, \description\: \Show
help
and
command
guide\}
            ]'''
c = c.replace(old_cmds, new_cmds)
