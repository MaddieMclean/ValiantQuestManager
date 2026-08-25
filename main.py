from typing import Optional
import json

from rich.prompt import Prompt, Confirm

from manager.console import console

from pathlib import Path

from manager.loop import game_loop

"""
CLI interface for running Valiant Quest, each location is stored in a linked list with the link to its neighbours

Should be able to:
- Save and load campaigns (stored as a json file)
- Track and give information about the current location
- Generate new locations on demand
- Travel to and explore locations
- Generate loot
- Generate market goods
- Check for random encounters during travel

Future:
- Generate dungeon floors on the fly
- Generate named monsters
- Generate and display stats for monsters in an encounter
- Faction management
"""

def load_data() -> Optional[dict]:
    save_dir = Path.home() / "ValiantQuestManager/"
    if not save_dir.exists():
        create_save_dir = Confirm.ask(f"Save directory {save_dir} does not exist, create?")
        if not create_save_dir:
            return

    save_dir.mkdir(parents=True, exist_ok=True)
    saves = {f.stem: f for f in save_dir.glob("*.json")}
    if not saves:
        console.print("No save files found.")
        return

    choice = Prompt.ask("Select save data to load", choices=list(saves.keys()))
    content = saves[choice].read_text("utf-8")
    return json.loads(content)


def main():
    # title page

    data = load_data()

    # load data model

    # start loop
    return game_loop()



if __name__ == '__main__':
    main()