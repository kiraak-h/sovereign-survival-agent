import sys

with open('server.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add Jinja2Templates import
import_stmt = 'from fastapi.responses import HTMLResponse'
new_import_stmt = 'from fastapi.responses import HTMLResponse\nfrom fastapi.templating import Jinja2Templates\nfrom fastapi import Request\n\ntemplates = Jinja2Templates(directory="templates")\n'
content = content.replace(import_stmt, new_import_stmt)

# Add the root endpoint to serve the dashboard
dashboard_endpoint = '''
@app.get("/", response_class=HTMLResponse, summary="Agent Public Dashboard")
def serve_dashboard(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
'''
content = content + dashboard_endpoint

with open('server.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Added web dashboard endpoint")
