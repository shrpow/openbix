from dataclasses import dataclass


class InvalidApiKeyError(Exception):
    ...


@dataclass
class CaptchaRecognitionProviderApiKey:
    api_key: str

    @staticmethod
    def from_string(api_key: str) -> "CaptchaRecognitionProviderApiKey":
        if not len(stripped_api_key := api_key.strip()) == 32:
            raise InvalidApiKeyError(api_key)

        return CaptchaRecognitionProviderApiKey(api_key=stripped_api_key)
