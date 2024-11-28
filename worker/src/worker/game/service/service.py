import asyncio
import random

from loguru import logger

from worker.captcha.dto import CaptchaResultDTO
from worker.captcha.service import CaptchaService, InvalidCaptchaSolutionError
from worker.game.core.game import Add, Config, Game, MapObjectConfig
from worker.game.core.map_object import MapObjectType
from worker.game.service.dto import GameResultDTO
from worker.moonbix_client import CaptchaNeededError, MoonbixClient


class CaptchaSolveAttemptsExceededError(Exception):
    ...


class GameService:
    __moonbix_client: MoonbixClient
    __captcha_service: CaptchaService

    def __init__(
        self, moonbix_client: MoonbixClient, captcha_service: CaptchaService
    ) -> None:
        self.__moonbix_client = moonbix_client
        self.__captcha_service = captcha_service

    async def play_game(
        self,
        access_token: str,
        telegram_user_id: int,
        start_timestamp: int,
        duration: int,
    ) -> GameResultDTO:
        captcha_result: CaptchaResultDTO | None = None

        for _ in range(10):
            try:
                game_data = await self.__moonbix_client.get_game(
                    access_token=access_token,
                    telegram_user_id=telegram_user_id,
                    captcha_data=captcha_result,
                )
                logger.debug(f"{telegram_user_id=} got game data")
                break
            except CaptchaNeededError as exc:
                logger.debug(f"{telegram_user_id=} captcha needed {exc.session_id=}")

                try:
                    captcha_result = await self.__captcha_service.solve_captcha(
                        session_id=exc.session_id
                    )
                except InvalidCaptchaSolutionError:
                    logger.debug(f"{telegram_user_id=} captcha solution is invalid")
                    continue

                logger.debug(
                    f"{telegram_user_id=} captcha solved {exc.session_id=} {captcha_result=}"
                )
                continue

        else:
            raise CaptchaSolveAttemptsExceededError

        logger.debug(f"{game_data.tag=} processing")

        game = Game.create(data=Add(tag=game_data.tag))
        game.set_map(
            data=game.generate_map(
                data=Config(
                    map_=random.sample(
                        [
                            MapObjectConfig(
                                size=map_object.size,
                                speed=map_object.speed,
                                type=MapObjectType(map_object.type),
                                reward=map_object.reward,
                            )
                            for map_object in game_data.map_
                        ],
                        8,
                    ),
                    duration=45,
                    hook_speed=300,
                    start_timestamp=start_timestamp,
                )
            )
        )
        result = game.generate_result(max_reward=150)
        result_plain_payload = ";".join(
            [map_object.as_string() for map_object in result.map_]
        )
        result_encrypted_payload = game.encrypt_timeline(
            tag=game_data.tag, stringified_timeline=result_plain_payload
        )
        game_result = GameResultDTO(
            encrypted_payload=result_encrypted_payload.data,
            score=result.score,
            plain_payload=result_plain_payload,
            aes_iv=result_encrypted_payload.iv,
            aes_key=result_encrypted_payload.key,
        )

        await asyncio.sleep(delay=duration)

        is_successful = await self.__moonbix_client.complete_game(
            access_token=access_token, result=game_result
        )

        logger.debug(f"{game.tag=} {is_successful=}")

        return game_result
