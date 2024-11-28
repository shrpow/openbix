from uuid import UUID

from aiogram import Bot, F, Router
from aiogram.types import CallbackQuery
from backend.invite.service import InviteService
from backend.telegram.invite.deeplink import DeeplinkPayload, create_deeplink
from backend.telegram.middleware import AuthorizationMiddleware
from backend.telegram.template.template import Template
from backend.user.dto import UserDTO


class InviteStatsRouter(Router):
    __bot: Bot
    __invite_service: InviteService
    __authorization_middleware: AuthorizationMiddleware

    def __init__(
        self,
        bot: Bot,
        invite_service: InviteService,
        authorization_middleware: AuthorizationMiddleware,
    ) -> None:
        super().__init__()

        self.__bot = bot
        self.__invite_service = invite_service
        self.__authorization_middleware = authorization_middleware

        self.name = "InviteStats"

        self.callback_query.middleware.register(self.__authorization_middleware)
        self.callback_query.register(self.send_invite_info, F.data == "invites/info")

    async def send_invite_info(self, query: CallbackQuery, user: UserDTO) -> None:
        user_deeplink = await create_deeplink(
            bot=self.__bot, payload=DeeplinkPayload(i=UUID(user.uuid))
        )
        invitee_count = await self.__invite_service.get_invitee_count(
            user=user, invited_user_id=user.uuid
        )
        await query.message.answer(  # type: ignore
            text=Template.INFO_PARTNERSIP_DETAILS.render(
                language=user.language,
                deeplink=user_deeplink,
                invitee_count=invitee_count,
            )
        )
