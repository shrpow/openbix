import binascii
import random
from base64 import b64encode
from dataclasses import dataclass

from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad

from worker.game.core.map_object import (
    MapObject,
    MapObjectAdd,
    MapObjectType,
)


@dataclass(slots=True)
class Add:
    tag: str


@dataclass(slots=True)
class MapObjectConfig:
    size: int
    speed: int
    type: MapObjectType
    reward: int


@dataclass(slots=True)
class Config:
    map_: list[MapObjectConfig]
    duration: int
    hook_speed: int
    start_timestamp: int


@dataclass(slots=True)
class Result:
    map_: list[MapObject]
    score: int


@dataclass(frozen=True, slots=True)
class AESEncryptedData:
    data: str
    iv: str
    key: str


@dataclass(slots=True)
class Game:
    tag: str
    map_: list[MapObject]

    @staticmethod
    def generate_random_int(min_: int, max_: int) -> int:
        return random.randrange(min_, max_)

    @staticmethod
    def create(data: Add) -> "Game":
        if not len(data.tag) == 32:
            raise ValueError("Game tag length should be 32")

        return Game(tag=data.tag, map_=[])

    def set_map(self, data: list[MapObject]) -> None:
        self.map_ = data

    def generate_map(self, data: Config) -> list[MapObject]:
        map_: list[MapObject] = []
        current_timestamp = data.start_timestamp

        for map_item in data.map_:
            current_timestamp += (
                (data.hook_speed // map_item.speed)
                + Game.generate_random_int(min_=2, max_=5)
            ) * 1000

            if current_timestamp >= data.start_timestamp + (data.duration * 1000):
                break

            game_object = MapObject.create(
                data=MapObjectAdd(
                    timestamp=current_timestamp,
                    size=map_item.size,
                    speed=map_item.speed,
                    type=map_item.type,
                    reward=map_item.reward,
                )
            )
            map_.append(game_object)

        return map_

    def __count_total_reward(self, timeline: list[MapObject]) -> int:
        reward = 0

        for item in timeline:
            reward = max(0, reward + item.reward)

        return reward

    def generate_result(self, max_reward: int) -> Result:
        timeline: list[MapObject] = []

        for map_item in sorted(self.map_, key=lambda item: item.timestamp):
            if self.__count_total_reward(timeline=timeline) >= max_reward:
                break

            timeline.append(map_item)

        total_reward = self.__count_total_reward(timeline=timeline)
        return Result(map_=timeline, score=total_reward)

    def encrypt_timeline(self, tag: str, stringified_timeline: str) -> AESEncryptedData:
        iv = b64encode(get_random_bytes(12))
        key = bytes.fromhex(binascii.hexlify(tag.encode()).decode())

        cipher = AES.new(key=key, mode=AES.MODE_CBC, iv=iv)
        result = cipher.encrypt(pad(stringified_timeline.encode(), AES.block_size))

        return AESEncryptedData(
            data=iv.decode() + b64encode(result).decode(),
            iv=iv.decode(),
            key=key.decode(),
        )
