from worker.captcha.core.captcha import Captcha

captcha = Captcha.create(
    image_path="/govno.png",
    tag="poo",
    session_id="a",
    encryption_key="abcd",
    signature="qwe",
    salt="12345",
)


def test_raw_payload_generation() -> None:
    assert captcha.generate_raw_payload(cell_positions=[1, 2]) == '{"dist": "0-1"}'


def test_xor_key_generation() -> None:
    assert captcha.generate_xor_key() == "dcbaayxk"


def test_payload_encryption() -> None:
    assert (
        captcha.encrypt_payload(xor_key="dcbaayxk", payload='{"dist": "0-1"}')
        == "H0EGCBINWlFEQVJMUFsF"
    )


def test_checksum_generation() -> None:
    assert captcha.generate_checksum(encrypted_payload="H0EGCBINWlFEQVJMUFsF") == "3905"
