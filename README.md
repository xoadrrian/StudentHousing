This is the EN11 group 1 GitHub repo for our project - Website for student housing where tenants manage chores and supplies, report issues, and chat with maintenance workers. Managers assign issues to workers.

## Project structure

| `main.py` | Starts the app and connects all the parts |
| `database.py` | Connects to the database using the link in `.env` |
| `models.py` | The database tables written as Python classes |
| `routers/` | The logic of the site, one file per feature (login, chores, inventory, tickets, chat) |
| `templates/` | The HTML pages users see |
| `static/` | CSS, JavaScript and images |
| `.env` | Database password. **Not on GitHub**, ask the team for it |
| `.gitignore` | Tells Git which files never to upload (`.venv`, `.env`, cache files) |
| `.venv/` | Your own Python setup. Each person creates it themselves, not on GitHub |

## Setup (first time)

1. **Clone the repo.** In GitHub Desktop: *File → Clone repository.
   This downloads the project to your computer.

2. **Open it in VS Code.** In GitHub Desktop: *Repository → Open in Visual Studio Code*.

3. **Create a virtual environment.** In the VS Code terminal:
   python -m venv .venv

   This makes a private Python for this project, so packages don't mix with other projects.

4. **Activate it.**
   Ctrl+Shift+P → Python: Select Interpreter → .venv
   You'll see `(.venv)` in the terminal.
   and VS Code activates it automatically in every new terminal.

5. **Install the packages.**

   pip install fastapi uvicorn sqlalchemy psycopg2-binary python-dotenv

   - `fastapi`: the web framework
   - `uvicorn`: runs the server
   - `sqlalchemy` + `psycopg2-binary`: talk to the database
   - `python-dotenv`: reads `.env`

6. **Create the `.env` file** in the main folder with the link the team sends you:
   Will be sent later


## Working together
1. **Pull first:** In GitHub Desktop, click *Fetch origin → Pull origin* to get the latest changes.
2. **New branch for each task:** *Current branch → New branch* (e.g. `feature/tickets`), so you don't break `main`.
3. **Commit and push:** Write a short summary, *Commit*, then *Push origin*.
4. **Pull request:** *Create Pull Request* on GitHub. A teammate checks it and merges it into `main`.

**Rules:** never commit `.env`, never work directly on `main`.