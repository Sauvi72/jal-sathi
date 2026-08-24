"""
main.py
Root entrypoint for Jal FastAPI Application.
Enables running `uvicorn main:app --reload --port 8000` or `python main.py`.
"""

from app.main import app

if __name__ == "__main__":
    import uvicorn
    from config import HOST, PORT, DEBUG
    uvicorn.run("main:app", host=HOST, port=PORT, reload=DEBUG)
