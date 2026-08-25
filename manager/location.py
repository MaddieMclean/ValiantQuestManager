from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum, IntEnum
from random import randint, sample
from typing import Optional

from dataclasses_json import dataclass_json
from rich.prompt import Confirm, Prompt

from manager.console import console

class LocationTypes(StrEnum):
    village = "Village"
    town = "Town"
    city = "City"
    castle = "Castle"
    landmark = "Landmark"
    dungeon = "Dungeon"
    stronghold = "Stronghold"

    @property
    def is_settlement(self) -> bool:
        return self in {
            LocationTypes.village,
            LocationTypes.town,
            LocationTypes.city,
            LocationTypes.castle,
        }

    @property
    def is_adventure_site(self) -> bool:
        return self in {
            LocationTypes.landmark,
            LocationTypes.dungeon,
            LocationTypes.stronghold,
        }


class Shop(IntEnum):
    witch = 1
    temple = 2
    bowyer = 3
    stable = 4
    smith = 5
    alchemist = 6
    armourer = 7
    mage_tower = 8

    def __str__(self) -> str:
        return self.name.replace("_", " ").title()

@dataclass
class Connection:
    distance: int
    name: str

@dataclass_json
@dataclass
class Location:
    # todo add a way of editing the name of a location in case of typos
    # todo add method of initialising a class based on save data (related to previous todo)

    name: str
    civ: int
    type: LocationTypes
    shops: Optional[list[Shop]] = None
    floors: Optional[int] = None
    connections: dict[str, int] = field(default_factory=dict)

    def __str__(self) -> str:
        text = [f"Name: {self.name}", f"Type: {self.type}"]
        if self.shops:
            text.append(f"Available Shops: {', '.join([str(s) for s in self.shops])}")

        if self.floors:
            text.append(f"Floors: {self.floors}")

        if self.connections:
            text.append(f"Connected to: {', '.join(self.connections.keys())}")

        return "\n".join(text)


def generate_location(
    neighbour: Optional[Connection],
    all_locations: dict[str, Location],
    civ: int,
    type_override: Optional[LocationTypes] = None,
) -> Location:
    # todo move user interactions out of generation logic
    # todo ideally, all cli interaction should happen outside generation logic
    # todo move append logic to be handled in another layer too
    location_type = type_override or _generate_type(civ, all_locations)
    location = Location(
        name=Prompt.ask("Please input location name:"),
        civ=civ,
        type=location_type,
        shops=_generate_shops(location_type),
        connections={neighbour.name: neighbour.distance} if neighbour else {}
    )
    location.floors = _generate_floors(location, all_locations)
    all_locations[location.name] = location
    return location


def explore(current_location: Location, all_locations: dict[str, Location]) -> list[Location]:
    new_paths = randint(1, 4)
    path_lengths = sorted((1 + randint(1, 3) for _ in range(new_paths)), reverse=True)

    connected_to_known_location = randint(1, 6) > 1
    connected_to_map_edge = randint(1, 6) > 3

    if connected_to_known_location and _confirm_connected("known location"):
        neighbour_name = Prompt.ask(
            "Input the name of the connected location",
            choices=list(all_locations.keys())
        )

        path_lengths = path_lengths
        neighbour_distance = path_lengths.pop()
        location = all_locations[neighbour_name]
        location.connections[current_location.name] = neighbour_distance
        current_location.connections[location.name] = neighbour_distance

    if len(path_lengths) > 0 and connected_to_map_edge and _confirm_connected("map edge"):
        # this won't break, even on an empty list
        path_lengths = path_lengths.pop()

    new_locations = []
    for distance in path_lengths:
        discovery = generate_location(Connection(distance, current_location.name), all_locations, current_location.civ)
        current_location.connections[discovery.name] = distance
        new_locations.append(discovery)

    return new_locations


def _generate_type(civ: int, all_locations: dict[str, Location]) -> LocationTypes:
    # Settlement
    if randint(1, 6) + civ > 3:
        number_of_villages = len(
            [l for l in all_locations.values() if l.type == LocationTypes.village]
        )
        if randint(1, 20) > number_of_villages:
            return LocationTypes.village

        match randint(1, 6) + civ:
            case 1 | 2 | 3:
                return LocationTypes.castle
            case 4 | 5:
                return LocationTypes.town
            case _:
                return LocationTypes.city

    # Adventure Site
    match randint(1, 6) + civ:
        case 1 | 2 | 3:
            return LocationTypes.landmark
        case 4 | 5:
            return LocationTypes.dungeon
        case _:
            return LocationTypes.stronghold


def _generate_shops(location_type: LocationTypes) -> Optional[list[Shop]]:
    if not location_type.is_settlement:
        return

    match location_type:
        case LocationTypes.village:
            return [Shop(randint(1, 4))]
        case LocationTypes.town:
            return [Shop(n) for n in sample(range(1, 7), 2)]
        case LocationTypes.city:
            return [Shop(n) for n in sample(range(1, 9), 4)]
        case LocationTypes.castle:
            return [Shop(1 + randint(1, 6))]


def _generate_floors(location: Location, all_locations: dict[str, Location]) -> Optional[int]:
    if not location.type.is_adventure_site:
        return

    match location.type:
        case LocationTypes.landmark:
            return 0
        case LocationTypes.dungeon:
            return _generate_dungeon_floors()
        case LocationTypes.stronghold:
            floors = randint(1, 3)
            if randint(1, 10) == 10:
                console.print("There is a Dungeon beneath the Stronghold, generating...")
                dungeon = generate_location(
                    Connection(0, location.name),
                    all_locations,
                    location.civ,
                    type_override=LocationTypes.dungeon,
                )
                location.connections[dungeon.name] = 0

            return floors


def _confirm_connected(connection: str) -> bool:
    """
    Since we don't simulate the map, we can only roll and see if a connection is possible.
    We need to confirm with the user whether an edge connects back to an existing location, or the map edge.
    """
    return Confirm.ask(f"Rolled a {connection} connection, apply? (yes/no)")


def _generate_dungeon_floors() -> int:
    floors = total_floors = randint(1, 4)
    while floors == 4:
        floors = randint(1, 4)
        total_floors += floors - 1

    return total_floors
