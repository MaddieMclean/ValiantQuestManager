from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, StrEnum
from random import randint, sample
from typing import Optional

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


class Shop(Enum):
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


class Location:
    # todo add a way of editing the name of a location in case of typos
    # todo separate the data into a dataclass, separate from the functions
    # todo add method of initialising a class based on save data (related to previous todo)

    name: str
    civ: int
    type: LocationTypes
    shops: Optional[list[Shop]]
    floors: Optional[int]
    connections: dict[str, int]

    def __init__(
        self,
        neighbour: Optional[Connection],
        all_locations: list[Location],
        civ: int,
        type_override: Optional[LocationTypes] = None,
    ):
        self.name = Prompt.ask("Please input location name:")
        self.civ = civ
        self.type = type_override or self._generate_type(all_locations)
        self.shops = self._generate_shops()
        self.floors = self._generate_floors(all_locations)
        self.connections = {neighbour.name: neighbour.distance} if neighbour else {}
        all_locations.append(self)

    def explore(self, all_locations: list[Location]) -> list[Location]:
        new_paths = randint(1, 4)
        path_lengths = [1 + randint(1, 3) for _ in range(new_paths)]

        connected_to_known_location = randint(1, 6) > 1
        connected_to_map_edge = randint(1, 6) > 3

        if connected_to_known_location and _confirm_connected("known location"):
            path_lengths = sorted(path_lengths, reverse=True)
            neighbour_distance = path_lengths.pop()
            neighbour_name = Prompt.ask("Input the name of the connected location")
            for location in all_locations:
                if location.name == neighbour_name:
                    location.connections[self.name] = neighbour_distance
                    self.connections[location.name] = neighbour_distance

        if connected_to_map_edge and _confirm_connected("map edge"):
            # this won't break, even on an empty list
            path_lengths = sorted(path_lengths, reverse=True)[:-1]

        new_locations = []
        for distance in path_lengths:
            location = Location(Connection(distance, self.name), all_locations, self.civ)
            self.connections[location.name] = distance
            new_locations.append(location)

        return new_locations

    def _generate_type(self, all_locations: list[Location]) -> LocationTypes:
        # Settlement
        if randint(1, 6) + self.civ > 3:
            number_of_villages = len(
                [l for l in all_locations if l.type == LocationTypes.village]
            )
            if randint(1, 20) > number_of_villages:
                return LocationTypes.village

            match randint(1, 6) + self.civ:
                case 1 | 2 | 3:
                    return LocationTypes.castle
                case 4 | 5:
                    return LocationTypes.town
                case _:
                    return LocationTypes.city

        # Adventure Site
        match randint(1, 6) + self.civ:
            case 1 | 2 | 3:
                return LocationTypes.landmark
            case 4 | 5:
                return LocationTypes.dungeon
            case _:
                return LocationTypes.stronghold

    def _generate_shops(self) -> Optional[list[Shop]]:
        if not self.type.is_settlement:
            return

        match self.type:
            case LocationTypes.village:
                return [Shop(randint(1, 4))]
            case LocationTypes.town:
                return [Shop(n) for n in sample(range(1, 7), 2)]
            case LocationTypes.city:
                return [Shop(n) for n in sample(range(1, 9), 4)]
            case LocationTypes.castle:
                return [Shop(1 + randint(1, 6))]

    def _generate_floors(self, all_locations: list[Location]) -> Optional[int]:
        if not self.type.is_adventure_site:
            return

        match self.type:
            case LocationTypes.landmark:
                return 0
            case LocationTypes.dungeon:
                return _generate_dungeon_floors()
            case LocationTypes.stronghold:
                floors = randint(1, 3)
                if randint(1, 10) == 10:
                    console.print("There is a Dungeon beneath the Stronghold, generating...")
                    new_location = Location(
                        Connection(0, self.name),
                        all_locations,
                        self.civ,
                        type_override=LocationTypes.dungeon,
                    )
                    self.connections[new_location.name] = 0

                return floors

    def __str__(self) -> str:
        text = [f"Name: {self.name}", f"Type: {self.type}"]
        if self.shops:
            text.append(f"Available Shops: {', '.join([str(s) for s in self.shops])}")

        if self.floors:
            text.append(f"Floors: {self.floors}")

        if self.connections:
            text.append(f"Connected to: {', '.join(self.connections.keys())}")

        return "\n".join(text)


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
