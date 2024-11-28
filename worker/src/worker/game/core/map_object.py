import enum
import random
from dataclasses import dataclass


class MapObjectType(enum.IntEnum):
    TRAP = 0
    REWARD = 1
    BONUS = 2


@dataclass(slots=True)
class MapObjectAdd:
    timestamp: int
    size: int
    speed: int
    type: MapObjectType
    reward: int


@dataclass(slots=True)
class MapObject:
    timestamp: int
    firing_x: float
    firing_y: float
    angle: float
    hook_x: float
    hook_y: float
    type: MapObjectType
    size: int
    reward: int
    reward_checksum: int
    tap_x: float
    tap_y: float

    @staticmethod
    def generate_random_float(
        min_: float, max_: float, decimal_places_num: int = 3
    ) -> float:
        return round(random.uniform(min_, max_), decimal_places_num)

    @staticmethod
    def create(data: MapObjectAdd) -> "MapObject":
        x = MapObject.generate_random_float(min_=10.0, max_=384.0)
        y = MapObject.generate_random_float(min_=100.0, max_=900.0)

        firing_x = x + MapObject.generate_random_float(min_=1.0, max_=5.0)
        firing_y = y + MapObject.generate_random_float(min_=1.0, max_=5.0)
        angle = MapObject.generate_random_float(min_=-1.0, max_=1.0)
        hook_x = firing_x - MapObject.generate_random_float(min_=1.0, max_=5.0)
        hook_y = firing_y - MapObject.generate_random_float(min_=1.0, max_=5.0)
        tap_x = MapObject.generate_random_float(min_=1.0, max_=384)
        tap_y = MapObject.generate_random_float(min_=1.0, max_=900)
        reward_checksum = data.size + abs(data.reward)

        return MapObject(
            timestamp=data.timestamp,
            firing_x=firing_x,
            firing_y=firing_y,
            angle=angle,
            hook_x=hook_x,
            hook_y=hook_y,
            type=data.type,
            size=data.size,
            reward=data.reward,
            reward_checksum=reward_checksum,
            tap_x=tap_x,
            tap_y=tap_y,
        )

    def as_string(self) -> str:
        return f"{self.timestamp}|{self.firing_x:.3f}|{self.firing_y:.3f}|{self.angle:.3f}|{self.hook_x:.3f}|{self.hook_y:.3f}|{self.type}|{self.size}|{self.reward_checksum}|{self.tap_x:.3f}|{self.tap_y:.3f}"
