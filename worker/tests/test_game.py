from datetime import datetime

from worker.game.core.game import Add, Config, Game, MapObjectConfig
from worker.game.core.map_object import MapObjectType

start_timestamp = round(datetime.now().timestamp() * 1000)

game = Game.create(data=Add(tag="asdfghjklqwertyuiopzxcvbnmeg2345"))
game_config = Config(
    map_=[
        MapObjectConfig(size=10, speed=100, type=MapObjectType.TRAP, reward=-100),
        MapObjectConfig(size=10, speed=100, type=MapObjectType.TRAP, reward=-100),
        MapObjectConfig(size=10, speed=100, type=MapObjectType.BONUS, reward=100),
    ],
    duration=45,
    hook_speed=100,
    start_timestamp=start_timestamp,
)
game_map = game.generate_map(data=game_config)
game.set_map(data=game_map)
end_timestamp = start_timestamp + (game_config.duration * 1000)


def test_map_generation() -> None:
    assert len(game_map) > 0


def test_map_serialization() -> None:
    assert len(game_map[0].as_string().split("|")) == 11


def test_map_timestamp_range() -> None:
    assert start_timestamp < game_map[0].timestamp < end_timestamp


def test_map_timestamp_chain() -> None:
    previous_timestamp: int = 0

    for item in game_map:
        assert item.timestamp > previous_timestamp
        previous_timestamp = item.timestamp


def test_map_object_reward_checksum() -> None:
    assert game_map[-1].reward_checksum == game_map[-1].size + game_map[-1].reward


def test_result_calculation() -> None:
    assert game.generate_result(max_reward=1000).score == 100
