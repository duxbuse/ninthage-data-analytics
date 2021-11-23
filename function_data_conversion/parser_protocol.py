from typing import List, Protocol


from data_classes import ArmyEntry
from typing import List


class Parser(Protocol):
    @staticmethod
    def parse_block(lines: List[str]) -> ArmyEntry:
        ...

