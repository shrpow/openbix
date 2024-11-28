import os


class Config:
    DB_CONNECTION_STRING: str = os.environ["FBX_DB_CONNECTION_STRING"]
    TG_NEWS_CHANNEL_NAME: str = os.environ["FBX_TG_NEWS_CHANNEL_NAME"]
    TG_SUPPORT_USERNAME: str = os.environ["FBX_TG_SUPPORT_USERNAME"]
    TG_GOD_USER_ID: int = int(os.environ["FBX_TG_GOD_USER_ID"])
    TG_BOT_TOKEN: str = os.environ["FBX_TG_BOT_TOKEN"]
    EMQ_WORKER_BALANCER_INPUT_ADDRESS: str = os.environ[
        "FBX_EMQ_WORKER_BALANCER_INPUT_ADDRESS"
    ]
    EMQ_WORKER_BALANCER_OUTPUT_ADDRESS: str = os.environ[
        "FBX_EMQ_WORKER_BALANCER_OUTPUT_ADDRESS"
    ]
    EMQ_WORKER_MESSAGE_BUS_ADDRESS: str = os.environ[
        "FBX_EMQ_WORKER_MESSAGE_BUS_ADDRESS"
    ]
