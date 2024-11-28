from dataclasses import dataclass

from backend.i18n.language import Language


@dataclass
class I18nContainer:
    ru: str
    en: str

    def get_value(self, language: Language) -> str:
        return {Language.RU: self.ru, Language.EN: self.en}.get(language, self.en)

    def get_values(self) -> list[str]:
        return [self.ru, self.en]
