# eisenhower

A lightweight local todo app built around the [Eisenhower matrix](https://en.wikipedia.org/wiki/Time_management#The_Eisenhower_Method), a simple framework for deciding what to work on by sorting tasks into four quadrants: urgent/important, not-urgent/important, urgent/not-important, and neither.

Runs entirely on your machine. Tasks are stored in a local SQLite database.

## Features

- Matrix view: drag tasks between the four quadrants (Do first, Schedule, Delegate, Eliminate) and an Inbox for unsorted items
- List view: flat sorted list of all open tasks with due dates and quadrant badges
- Projects: group tasks into named project columns; drag tasks between them
- Due dates: append a `YYYY-MM-DD` date when capturing a task; click to edit inline
- Inline editing: click any task text to edit it in place
- Completed tab: mark tasks done, review history, or restore tasks to active

## Installation

Requires Python 3.13+ and [uv](https://docs.astral.sh/uv/).

```bash
# clone this git repo
git clone <repo-url>

# change to the eisenhower directory
cd eisenhower

# install the dependencies with uv
uv sync

# run the fastAPI app on port 5858
uv run uvicorn app:app --host 127.0.0.1 --port 5858
```

Then open http://localhost:5858 in your browser.

### Run as a background service (systemd)

```bash
cp eisenhower.service.example ~/.config/systemd/user/eisenhower.service
# Edit WorkingDirectory and ExecStart paths to match your setup
systemctl --user enable --now eisenhower
```

## Usage

Adding a task: type in the top bar and press Enter. Append a date to set a due date:

```
Fix login bug 2026-07-15
```

Sorting tasks: drag the grip handle on the left of a card to move it to a different quadrant.

Editing: click a task's text or due date to edit inline; press Enter or click away to save.

Completing: click the checkbox on a card. Find completed tasks under the Completed tab.

Projects: switch to the Projects tab, type a name and press Enter to create a project. Drag tasks from the "No project" column into any project. Use Close to archive a project; reopen it via "Show closed projects".
