import os


class Config:
    EMQ_WORKER_BALANCER_OUTPUT_ADDRESS: str = os.environ[
        "FBX_EMQ_WORKER_BALANCER_OUTPUT_ADDRESS"
    ]
    EMQ_WORKER_MESSAGE_BUS_ADDRESS: str = os.environ[
        "FBX_EMQ_WORKER_MESSAGE_BUS_ADDRESS"
    ]
