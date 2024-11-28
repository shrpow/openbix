import json
import urllib
import urllib.parse
from base64 import b64encode
from dataclasses import dataclass


@dataclass(slots=True)
class Captcha:
    image_url: str
    task_condition: str

    session_id: str
    encryption_key: str
    signature: str
    salt: str

    @staticmethod
    def create(
        image_path: str,
        tag: str,
        session_id: str,
        encryption_key: str,
        signature: str,
        salt: str,
    ) -> "Captcha":
        return Captcha(
            image_url=f"https://staticrecap.cgicgi.io{image_path}",
            task_condition=tag,
            session_id=session_id,
            encryption_key=encryption_key,
            signature=signature,
            salt=salt,
        )

    def generate_raw_payload(self, cell_positions: list[int]) -> str:
        return json.dumps(
            {
                "dist": "-".join([str(cell - 1) for cell in cell_positions]),
            }
        )

    def generate_xor_key(self) -> str:
        reversed_ek = self.encryption_key[::-1]
        needed_symbols_count = 4
        available_chars = "abcdhijkxy"

        return reversed_ek + "".join(
            [
                available_chars[(ord(reversed_ek[i]) * 31) % len(available_chars)]
                for i in range(needed_symbols_count)
            ]
        )

    def encrypt_payload(self, xor_key: str, payload: str) -> str:
        return b64encode(
            "".join(
                [
                    chr(ord(symbol) ^ ord(xor_key[i % len(xor_key)]))
                    for i, symbol in enumerate(payload)
                ]
            ).encode()
        ).decode()

    def generate_checksum(self, encrypted_payload: str) -> str:
        return str(
            sum(
                [
                    ord(symbol)
                    for symbol in f"tg_mini_game_play{self.signature}{encrypted_payload}{self.salt}"
                ]
            )
        )

    def generate_solution(self, cell_positions: list[int]) -> str:
        raw_payload = self.generate_raw_payload(cell_positions=cell_positions)
        encrypted_payload = self.encrypt_payload(
            xor_key=self.generate_xor_key(), payload=raw_payload
        )
        checksum = self.generate_checksum(encrypted_payload=encrypted_payload)

        return f"bizId=tg_mini_game_play&sv=20220812&lang=en&securityCheckResponseValidateId={self.session_id}&clientType=web&data={urllib.parse.quote(encrypted_payload)}&s={checksum}&sig={self.signature}"
