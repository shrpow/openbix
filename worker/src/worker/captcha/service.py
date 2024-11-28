from worker.captcha.core.captcha import Captcha
from worker.captcha.dto import CaptchaResultDTO
from worker.captcha_recognition_client import ICaptchaRecognitionClient
from worker.commonservice_client import CommonserviceClient


class InvalidCaptchaSolutionError(Exception):
    session_id: str

    def __init__(self, *args: object, session_id: str) -> None:
        super().__init__(*args)
        self.session_id = session_id


class CaptchaService:
    __captcha_recognition_service: ICaptchaRecognitionClient
    __commonservice_client: CommonserviceClient

    def __init__(
        self,
        captcha_recognition_service: ICaptchaRecognitionClient,
        commonservice_client: CommonserviceClient,
    ) -> None:
        self.__captcha_recognition_service = captcha_recognition_service
        self.__commonservice_client = commonservice_client

    async def solve_captcha(self, session_id: str) -> CaptchaResultDTO:
        captcha_data = await self.__commonservice_client.get_captcha(
            session_id=session_id
        )
        captcha = Captcha.create(
            image_path=captcha_data.image_path,
            tag=captcha_data.task_condition,
            session_id=session_id,
            encryption_key=captcha_data.encryption_key,
            signature=captcha_data.signature,
            salt=captcha_data.salt,
        )
        cell_positions = (
            await self.__captcha_recognition_service.get_grid_captcha_solution(
                image=await self.__commonservice_client.download_captcha_image(
                    image_url=captcha.image_url
                ),
                task_condition=captcha.task_condition,
                rows_count=3,
                cols_count=3,
            )
        )
        solution = captcha.generate_solution(cell_positions=cell_positions)

        validation_result = await self.__commonservice_client.validate_captcha(
            solution=solution
        )

        if not validation_result:
            raise InvalidCaptchaSolutionError(session_id=session_id)

        return CaptchaResultDTO(
            session_id=session_id,
            token=validation_result,
            challenge=validation_result.split("-")[1],
        )
