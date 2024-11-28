from datetime import datetime
from typing import Any, MutableMapping

import jinja2
from backend.game_account.dto import GameAccountDTO
from backend.i18n.language import Language
from backend.subscription.dto import SubscriptionDTO
from backend.tariff.dto import TariffDTO
from backend.telegram.template.utils import (
    prettify_timedelta,
    simplify_hours,
    strftime,
    to_skeleton,
)
from backend.user.dto import UserDTO


class StringLoader(jinja2.BaseLoader):
    __templates: dict[str, jinja2.Template] = {}

    def load(
        self,
        environment: jinja2.Environment,
        name: str,
        globals: MutableMapping[str, Any] | None = None,
    ) -> jinja2.Template:
        if not (template := self.__templates.get(name)):
            code = environment.compile(source=name)
            template = self.__templates[name] = jinja2.Template.from_code(
                environment=environment, code=code, globals=globals or {}
            )

        return template


class BaseTemplate:
    __env = jinja2.Environment(loader=StringLoader(), trim_blocks=True)
    __env.filters["simplify_hours"] = simplify_hours
    __env.filters["strftime"] = strftime
    __env.filters["prettify_timedelta"] = prettify_timedelta

    content: dict[Language, str]

    def render(self, language: Language, *args, **kwargs) -> str:
        return (
            self.__env.get_template(name=self.content[language])
            .render(**kwargs)
            .replace("    ", "")
        )

    def render_skeleton(self, language: Language) -> str:
        return (
            self.__env.get_template(
                name=f"<span class='tg-spoiler'>{to_skeleton(content=self.content[language], placeholder="🤔")}</span>"
            )
            .render()
            .replace("    ", "")
        )


class MainMenuTemplate(BaseTemplate):
    content: dict[Language, str] = {
        Language.RU: "🧶 Главное меню",
        Language.EN: "🧶 Main menu",
    }

    def render(self, language: Language) -> str:
        return super().render(language=language)


class GreetingTemplate(BaseTemplate):
    content: dict[Language, str] = {Language.RU: "👋 Привет!", Language.EN: "👋 Hello!"}

    def render(self, language: Language) -> str:
        return super().render(language=language)


class NoSubscriptionAlertTemplate(BaseTemplate):
    content: dict[Language, str] = {
        Language.RU: "Похоже, у тебя нет активной подписки — приобрети её у {{ support }}!",
        Language.EN: "It looks like you don't have an active subscription — purchase it from {{ support }}!",
    }

    def render(self, language: Language, support: str) -> str:
        return super().render(language, support=support)


class SubscriptionDetailsTemplate(BaseTemplate):
    content: dict[Language, str] = {
        Language.RU: "Подписка ({subscription.uuid})",
        Language.EN: "Subscription ({subscription.uuid})",
    }

    def render(self, language: Language, subscription: SubscriptionDTO) -> str:
        return super().render(language=language, subscription=subscription)


class LanguageQuestionTemplate(BaseTemplate):
    content: dict[Language, str] = {
        Language.RU: "🌎 Выбери язык",
        Language.EN: "🌎 Select a language",
    }

    def render(self, language: Language) -> str:
        return super().render(language=language)


class PartnershipDetailsTemplate(BaseTemplate):
    content: dict[Language, str] = {
        Language.RU: """
            💸 Партнёрская программа
            Приглашай пользователей и получай 10% от стоимости их покупок!

            <a href="{{ deeplink }}">🔗 Твоя ссылка-приглашение</a>
            Всего рефералов: {{ invitee_count }}

            <i>Баланс находится во вкладке "Мой профиль"</i>
        """,
        Language.EN: """
            💸 Affiliate Program
            Invite users and get 10% of the cost of their purchases!

            <a href="{{ deeplink }}">🔗 Your invitation link</a>
            Total referrals: {{ invitee_count }}

            <i>The balance is in the "My Profile" tab</i>
        """,
    }

    def render(self, language: Language, deeplink: str, invitee_count: int) -> str:
        return super().render(
            language=language, deeplink=deeplink, invitee_count=invitee_count
        )


class UserProfileTemplate(BaseTemplate):
    content: dict[Language, str] = {
        Language.RU: """
            👤 Профиль пользователя
            Баланс: {{ user.balance }}
            {% if subscription %}
                {% if subscription.active_until %}
                    Подписка действительна до {{ subscription.active_until | strftime("%d.%m.%Y %H:%M") }} ({{ tariff.name.ru }})
                {% else %}
                    Подписка действительна до заката солнца в выдуманном твоим вычурным сознанием мире ({{ tariff.name.ru }})
                {% endif %}
            {% else %}
                Пока подписки нет
            {% endif %}
            ID: <code>{{ user.uuid }}</code>
            Дата регистрации: {{ user.created_at | strftime("%d.%m.%Y %H:%M") }}
        """,
        Language.EN: """
            👤 User Profile
            Balance: {{ user.balance }}
            {% if subscription %}
                {% if subscription.active_until %}
                    Subscription is valid until {{ subscription.active_until | strftime("%m/%d/%Y %H:%M") }} ({{ tariff.name.en }})
                {% else %}
                    Subscription is valid for the rest of your life
                {% endif %}
            {% else %}
                No subscription yet
            {% endif %}
            ID: <code>{{ user.uuid }}</code>
            Registered at: {{ user.created_at | strftime("%m/%d/%Y %H:%M") }}
        """,
    }

    def render(
        self,
        language: Language,
        user: UserDTO,
        tariff: TariffDTO | None,
        subscription: SubscriptionDTO | None,
    ) -> str:
        return super().render(
            language=language, user=user, tariff=tariff, subscription=subscription
        )


class UserFoundSummaryTemplate(BaseTemplate):
    content: dict[Language, str] = {
        Language.RU: """
            👤 Пользователь найден
            ID: <code>{{ user.uuid }}</code>
            {% if subscription %}
                {% if subscription.active_until %}
                    Подписка действительна до {{ subscription.active_until | strftime("%d.%m.%Y %H:%M") }} ({{ tariff.name.ru }})
                {% else %}
                    Подписка действительна всегда
                {% endif %}
            {% else %}
                Пока подписки нет
            {% endif %}
        """,
        Language.EN: """
            👤 The user has been found
            ID: <code>{{ user.uuid }}</code>
            {% if subscription %}
                {%if subscription.active_until %}
                    Subscription is valid until {{ subscription.active_until | strftime("%m/%d/%Y %H:%M") }} ({{ tariff.name.ru }})
                {% else %}
                    The subscription is valid forever
                {% endif %}
            {% else %}
                There is no subscription yet
            {% endif %}
        """,
    }

    def render(
        self, language: Language, user: UserDTO, subscription: SubscriptionDTO | None
    ) -> str:
        return super().render(language, user=user, subscription=subscription)


class TariffSelectTemplate(BaseTemplate):
    content: dict[Language, str] = {
        Language.RU: "👾 Выбери тариф",
        Language.EN: "👾 Choose a tariff",
    }

    def render(self, language: Language) -> str:
        return super().render(language)


class AvailableTariffsTemplate(BaseTemplate):
    content: dict[Language, str] = {
        Language.RU: """
            👾 Доступные тарифы
            Нажмите одну из кнопок ниже, чтобы купить подписку
        """,
        Language.EN: """
            👾 Available tariffs
            Click one of the buttons below to buy a subscription
        """,
    }

    def render(self, language: Language) -> str:
        return super().render(language=language)


class UserTelegramIdQuestionTemplate(BaseTemplate):
    content: dict[Language, str] = {
        Language.RU: "🆔 Отправь мне Telegram ID пользователя",
        Language.EN: "🆔 Send me the telegram user id",
    }

    def render(self, language: Language) -> str:
        return super().render(language=language)


class InvalidTelegramIdTemplate(BaseTemplate):
    content: dict[Language, str] = {
        Language.RU: "⛔️ Некорректный Telegram ID. Попробуй другой",
        Language.EN: "⛔️ Invalid Telegram ID. Try another one",
    }

    def render(self, language: Language) -> str:
        return super().render(language=language)


class UserNotFoundTemplate(BaseTemplate):
    content: dict[Language, str] = {
        Language.RU: "⛔️ Пользователь не найден. Попробуй ещё раз",
        Language.EN: "⛔️ User not found. Try again",
    }

    def render(self, language: Language) -> str:
        return super().render(language=language)


class UserAlreadyHasSubscriptionTemplate(BaseTemplate):
    content: dict[Language, str] = {
        Language.RU: "ℹ️ У пользователя есть активная подписка",
        Language.EN: "ℹ️ The user has an active subscription",
    }

    def render(self, language: Language) -> str:
        return super().render(language=language)


class LanguageSetTemplate(BaseTemplate):
    content: dict[Language, str] = {
        Language.RU: "✅ Установлен русский язык",
        Language.EN: "✅ The English language is set",
    }

    def render(self, language: Language) -> str:
        return super().render(language=language)


class TariffInfoTemplate(BaseTemplate):
    content: dict[Language, str] = {
        Language.RU: """
            {{ tariff.name }}
        """,
        Language.EN: "✅ The English language is set",
    }

    def render(self, language: Language) -> str:
        return super().render(language=language)


class TariffItemTemplate(BaseTemplate):
    content: dict[Language, str] = {
        Language.RU: "{{ tariff.name.ru }} (${{ tariff.price }} на {{ (tariff.subscription_duration | simplify_hours).ru }}, до {{ tariff.max_game_accounts }} акк. MBX)",
        Language.EN: "{{ tariff.name.en }} (${{ tariff.price }} for {{ (tariff.subscription_duration | simplify_hours).en }}, up to {{ tariff.max_game_accounts }} MBX accounts)",
    }

    def render(self, language: Language, tariff: TariffDTO) -> str:
        return super().render(language=language, tariff=tariff)


class SubscriptionPreviewTemplate(BaseTemplate):
    content: dict[Language, str] = {
        Language.RU: """
            Выбран тариф {{ tariff.name.ru }}
            Стоимость: ${{ tariff.price }} {{ "(Если вывести бонусы, $"+ discount_price + ")" if tariff.price > 0 and discount_price != "-" else ""}}
            <i>Подписка будет создана только после выбора действия</i>
        """,
        Language.EN: """
            The selected tariff is {{ tariff.name.en }}
            Cost: ${{ tariff.price }} {{ "(If you withdraw bonuses, $"+ discount_price + ")" if tariff.price > 0 and discount_price != "-" else ""}}
            <i>The subscription will be created only after selecting the action</i>
        """,
    }

    def render(
        self,
        language: Language,
        user: UserDTO,
        tariff: TariffDTO,
        subscription: SubscriptionDTO,
        discount_price: str,
    ) -> str:
        return super().render(
            language=language,
            user=user,
            tariff=tariff,
            subscription=subscription,
            discount_price=discount_price,
        )


class SubscriptionIssuedTemplate(BaseTemplate):
    content: dict[Language, str] = {
        Language.RU: "✅ Подписка успешно выдана!",
        Language.EN: "✅ The subscription has been successfully issued!",
    }

    def render(self, language: Language) -> str:
        return super().render(language=language)


class SubscriptionCongratulationTemplate(BaseTemplate):
    content: dict[Language, str] = {
        Language.RU: """
            🥳 Благодарим за приобретение подписки!
            {% if subscription.active_until %}
                Она будет действовать до {{ subscription.active_until | strftime("%d.%m.%Y %H:%M") }}
            {% else %}
                Она будет действовать всегда
            {% endif%}
            Тариф: {{ tariff.name.ru }}
        """,
        Language.EN: """
            🥳 Thank you for purchasing a subscription!
            {% if subscription.active_until %}
                It will be valid until {{ subscription.active_until | strftime("%m/%d/%Y %H:%M") }}
            {% else %}
                It will valid for infinity
            {% endif%}
            Tariff: {{ tariff.name.en }}
        """,
    }

    def render(
        self, language: Language, tariff: TariffDTO, subscription: SubscriptionDTO
    ) -> str:
        return super().render(
            language=language, tariff=tariff, subscription=subscription
        )


class GameAccountDetailsTemplate(BaseTemplate):
    content: dict[Language, str] = {
        Language.RU: """
            {{ offset }}/{{ total_count }}. Аккаунт {{ game_account.name | e }}
            Статус: {{ "🟢 Активен" if game_account.status == "active" else "⚫️ Неактивен" }}
            Баланс: {{ game_account.balance or "-" }}
            Последний вход: {{ ((current_time - game_account.last_login_at) | prettify_timedelta).ru + " назад" if game_account.last_login_at else "-" }} 
            Прокси: <code>{{ game_account.proxy }}</code>
        """,
        Language.EN: """
            {{ offset }}/{{ total_count }}. Account {{ game_account.name | e }}
            Status: {{ "🟢 Active" if game_account.status == "active" else "⚫️ Inactive" }}
            Balance: {{ game_account.balance or "-" }}
            Last login: {{ ((current_time - game_account.last_login_at) | prettify_timedelta).en + " ago" if game_account.last_login_at else "-" }} 
            Proxy: <code>{{ game_account.proxy }}</code>
        """,
    }

    def render(
        self,
        language: Language,
        offset: int,
        total_count: int,
        game_account: GameAccountDTO,
        current_time: datetime,
    ) -> str:
        return super().render(
            language,
            offset=offset,
            total_count=total_count,
            game_account=game_account,
            current_time=current_time,
        )


class NoGameAccountsTemplate(BaseTemplate):
    content: dict[Language, str] = {
        Language.RU: "∅ Аккаунты не найдены. Добавьте их, и они здесь появятся!",
        Language.EN: "∅ No accounts found. Add them and they will appear here!",
    }

    def render(self, language: Language) -> str:
        return super().render(language)


class GameAccountCannotBeCreatedTemplate(BaseTemplate):
    content: dict[Language, str] = {
        Language.RU: "⛔️ Ошибка: Исчерпан лимит тарифа или нет активной подписки",
        Language.EN: "⛔️ Error: The tariff limit has been reached or you do not have an active subscription",
    }

    def render(self, language: Language) -> str:
        return super().render(language)


class GameAccountNameTemplate(BaseTemplate):
    content: dict[Language, str] = {
        Language.RU: "🏷️ Введи имя аккаунта, так тебе будет удобнее находить нужный в большом списке (1-30 символов)",
        Language.EN: "🏷️ Enter the account name, so it will be easier for you to find the one you need in a large list (1-30 characters)",
    }

    def render(self, language: Language) -> str:
        return super().render(language)


class InvalidAccountNameTemplate(BaseTemplate):
    content: dict[Language, str] = {
        Language.RU: "⛔️ Некорректное имя аккаунта. Попробуй заново",
        Language.EN: "⛔️ Incorrect account name. Try again",
    }

    def render(self, language: Language) -> str:
        return super().render(language)


class GameAccountWebAppLinkTutorialTemplate(BaseTemplate):
    content: dict[Language, str] = {
        Language.RU: """
            🔗 Отправь ссылку от Telegram WebApp
            Для этого нужно:
            1. Включить режим отладки WebApp (<a href="https://core.telegram.org/bots/webapps#debug-mode-for-mini-apps">официальная документация</a>)
            2. Открыть веб-приложение игры и запустить отладчик (пкм -> проверить элемент или f12)
            3. Зайти во вкладку <b>Console</b>, отправить команду <code>window.location.href</code> и скопировать URL <b>полностью</b>.
        """,
        Language.EN: """
            🔗 Send a link from Telegram WebApp
            To do this:
            1. Enable WebApp debugging mode (<a href="https://core.telegram.org/bots/webapps#debug-mode-for-mini-apps ">official documentation</a>)
            2. Open the game and run the debugger (right mouse click -> check element or f12)
            3. Go to the <b>Console</b> tab, send the command <code>window.location.href</code> and copy the URL <b>completely</b>.
        """,
    }

    def render(self, language: Language) -> str:
        return super().render(language)


class InvalidGameAccountWebAppLinkTemplate(BaseTemplate):
    content: dict[Language, str] = {
        Language.RU: "⛔️ Некорректная ссылка. Попробуй заново",
        Language.EN: "⛔️ Incorrect link. Try again",
    }

    def render(self, language: Language) -> str:
        return super().render(language)


class GameAccountProxyQuestionTemplate(BaseTemplate):
    content: dict[Language, str] = {
        Language.RU: """
            🕶️ Отправь один прокси для работы с аккаунтом
            Поддерживаемые протоколы: socks4, socks5, http, https
            Формат: protocol://[username:password@]ip[:port]
            <i>Фрагменты [между скобок] опциональны</i>
        """,
        Language.EN: """
            🕶️ Send one proxy to work with your account
            Supported protocols: socks4, socks5, http, https
            Format: protocol://[username:password@]ip:port
            <i>Fragments [between brackets] are optional</i>
        """,
    }

    def render(self, language: Language) -> str:
        return super().render(language)


class InvalidGameAccountProxyTemplate(BaseTemplate):
    content: dict[Language, str] = {
        Language.RU: "⛔️ Некорректный прокси. Попробуй заново",
        Language.EN: "⛔️ Incorrect proxy. Try again",
    }

    def render(self, language: Language) -> str:
        return super().render(language)


class CaptchaRecognitionProviderApiKeyQuestionTemplate(BaseTemplate):
    content: dict[Language, str] = {
        Language.RU: """🔑 Укажи API-ключ для работы с сервисом <a href="https://2captcha.com/?from=21763837">2captcha (aka rucaptcha)</a>""",
        Language.EN: """🔑 Specify the API key for working with the <a href="https://2captcha.com/?from=21763837">2captcha</a> service""",
    }

    def render(self, language: Language) -> str:
        return super().render(language)


class InvalidCaptchaRecognitionProviderApiKeyTemplate(BaseTemplate):
    content: dict[Language, str] = {
        Language.RU: "⛔️ Некорректный API-ключ. Попробуй заново",
        Language.EN: "⛔️ Incorrect API key. Try again",
    }

    def render(self, language: Language) -> str:
        return super().render(language)


class InvalidGameAccountLoginInfoTemplate(BaseTemplate):
    content: dict[Language, str] = {
        Language.RU: "⛔️ Некорректные данные для работы с аккаунтом. Попробуй заново",
        Language.EN: "⛔️ Incorrect data for working with the account. Try again",
    }

    def render(self, language: Language) -> str:
        return super().render(language)


class InvalidGameAccountSomethingTemplate(BaseTemplate):
    content: dict[Language, str] = {
        Language.RU: "⛔️ Что-то пошло не так: Возможно, этот аккаунт уже добавлен. Может быть, неподходящий прокси, нет активной подписки, неправильный API-ключ rucaptcha/2captcha или исчерпан лимит тарифа",
        Language.EN: "⛔️ Something went wrong: This account may have already been added. There may be an unsuitable proxy, there is no active subscription, invalid rucaptcha/2captcha API key or the tariff limit has been reached",
    }

    def render(self, language: Language) -> str:
        return super().render(language)


class GameAccountCreateCongratulationTemplate(BaseTemplate):
    content: dict[Language, str] = {
        Language.RU: "🥳 Аккаунт добавлен успешно!",
        Language.EN: "🥳 The account has been added succesfully!",
    }

    def render(self, language: Language) -> str:
        return super().render(language)


class ParticipiationNeededTemplate(BaseTemplate):
    content: dict[Language, str] = {
        Language.RU: "✋ Чтобы использовать этот функционал, подпишись на канал {{ channel_name }}, а затем попробуй снова",
        Language.EN: "✋ To use this functionality, subscribe to the {{ channel_name }} channel and then try again",
    }

    def render(self, language: Language, channel_name: str) -> str:
        return super().render(language, channel_name=channel_name)


class Template:
    INFO_MAIN_MENU = MainMenuTemplate()
    INFO_USER_PROFILE = UserProfileTemplate()
    INFO_TARIFFS = AvailableTariffsTemplate()
    INFO_TARIFF_ITEM = TariffItemTemplate()
    INFO_SUBSCRIPTION_DETAILS = SubscriptionDetailsTemplate()
    INFO_PARTNERSIP_DETAILS = PartnershipDetailsTemplate()
    INFO_SUBSCRIPTION_PREVIEW = SubscriptionPreviewTemplate()
    INFO_GAME_ACCOUNT = GameAccountDetailsTemplate()
    NOTIFICATION_GREETING = GreetingTemplate()
    NOTIFICATION_NO_SUBSCRIPTION = NoSubscriptionAlertTemplate()
    NOTIFICATION_INVALID_TELEGRAM_ID = InvalidTelegramIdTemplate()
    NOTIFICATION_USER_FOUND = UserFoundSummaryTemplate()
    NOTIFICATION_USER_NOT_FOUND = UserNotFoundTemplate()
    NOTIFICATION_USER_ALREADY_HAS_SUBSCRIPTION = UserAlreadyHasSubscriptionTemplate()
    NOTIFICATION_LANGUAGE_SET = LanguageSetTemplate()
    NOTIFICATION_SUBSCRIPTION_ISSUED = SubscriptionIssuedTemplate()
    NOTIFICATION_SUBSCRIPTION_PURCHASED = SubscriptionCongratulationTemplate()
    NOTIFICATION_NO_GAME_ACCOUNTS_ADDED = NoGameAccountsTemplate()
    NOTIFICATION_GAME_ACCOUNT_CANNOT_BE_CREATED = GameAccountCannotBeCreatedTemplate()
    NOTIFICATION_INVALID_GAME_ACCOUNT_NAME = InvalidAccountNameTemplate()
    NOTIFICATION_INVALID_WEB_APP_LINK = InvalidGameAccountWebAppLinkTemplate()
    NOTIFICATION_INVALID_PROXY = InvalidGameAccountProxyTemplate()
    NOTIFICATION_INVALID_LOGIN_INFO = InvalidGameAccountLoginInfoTemplate()
    NOTIFICATION_INVALID_SOMETHING = InvalidGameAccountSomethingTemplate()
    NOTIFICATION_INVALID_CAPTCHA_RECOGNITION_PROVIDER_API_KEY = (
        InvalidCaptchaRecognitionProviderApiKeyTemplate()
    )
    NOTIFICATION_GAME_ACCOUNT_CREATED = GameAccountCreateCongratulationTemplate()
    NOTIFICATION_PARTICIPIATION_NEEDED = ParticipiationNeededTemplate()
    QUESTION_LANGUAGE = LanguageQuestionTemplate()
    QUESTION_USER_TELEGRAM_ID = UserTelegramIdQuestionTemplate()
    QUESTION_TARIFF = TariffSelectTemplate()
    QUESTION_GAME_ACCOUNT_NAME = GameAccountNameTemplate()
    QUESTION_GAME_ACCOUNT_WEB_APP_LINK = GameAccountWebAppLinkTutorialTemplate()
    QUESTION_GAME_ACCOUNT_PROXY = GameAccountProxyQuestionTemplate()
    QUESTION_CAPTCHA_RECOGNITION_PROVIDER_API_KEY = (
        CaptchaRecognitionProviderApiKeyQuestionTemplate()
    )
