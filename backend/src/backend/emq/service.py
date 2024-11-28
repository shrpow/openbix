import asyncio
from collections import defaultdict
from collections.abc import Callable
from dataclasses import asdict
from typing import Coroutine

import zmq
import zmq.asyncio
import zmq.utils

from backend.core.message import AbstractMessage
from backend.core.utils import generate_uuid
from backend.emq.dto import EMQMessageDTO


class ExternalMQService:
    __node_id: str
    __zmq_context: zmq.asyncio.Context
    __recipients: dict[str, list[Callable[..., Coroutine]]]

    def __init__(self) -> None:
        self.__node_id = generate_uuid()
        self.__zmq_context = zmq.asyncio.Context()
        self.__recipients = defaultdict(list)

    @property
    def node_id(self):
        return self.__node_id

    async def start_broker(self, input_address: str, output_address: str) -> None:
        frontend = self.__zmq_context.socket(zmq.ROUTER)
        frontend.bind(input_address)

        backend = self.__zmq_context.socket(zmq.DEALER)
        backend.bind(output_address)

        await asyncio.get_event_loop().run_in_executor(
            None, zmq.proxy, frontend, backend
        )

    def on_message(
        self, message_type: type[AbstractMessage], callback: Callable[..., Coroutine]
    ) -> None:
        self.__recipients[message_type.__name__].append(callback)

    async def start_listener(self, address: str) -> None:
        socket = self.__zmq_context.socket(socket_type=zmq.REP)

        socket.bind(addr=address)
        # try:
        # except zmq.ZMQError:
        #     socket.connect(addr=address)

        while 1:
            try:
                message = EMQMessageDTO(**await socket.recv_json())  # type: ignore
            except Exception as exc:
                continue

            for recipient in self.__recipients[message.type]:
                asyncio.create_task(recipient(data=message.message))

            await socket.send(data=b"ok")

    async def send_message(
        self, recipient_input_address: str, message: AbstractMessage
    ) -> None:
        socket = self.__zmq_context.socket(socket_type=zmq.REQ)
        socket.connect(addr=recipient_input_address)

        socket.send_json(
            obj=asdict(
                EMQMessageDTO(type=message.__class__.__name__, message=asdict(message))
            )
        )

        await socket.recv()
        socket.close()
