from dataclasses import dataclass


class InvalidNameError(Exception):
    ...


@dataclass
class Name:
    name: str

    @staticmethod
    def from_string(name: str) -> "Name":
        if not 1 <= len(name) <= 30:
            raise InvalidNameError(name)

        return Name(name=name.strip())
