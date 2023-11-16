from enum import Enum
import json


class ZigZagMessageType(int, Enum):
    HEARTBEAT = 0
    PAIR_REQUEST = 1
    PAIR_CONFIRM = 2
    BEARER = 3


class ZigZagMessage:
    source_id: int
    destination_id: int
    next_waypoint_id: int
    last_waypoint_id: int
    data_length: int
    reversed_flag: bool
    message_type: ZigZagMessageType

    def __init__(self, messageType: ZigZagMessageType, content: int) -> None:
        self.messageType = messageType
        self.content = content

    def __init__(
        self,
        source_id: int = -1,
        destination_id: int = -1,
        next_waypoint_id: int = -1,
        last_waypoint_id: int = -1,
        data_length: int = 5,
        reversed_flag: bool = False,
        message_type: ZigZagMessageType = ZigZagMessageType.HEARTBEAT,
    ) -> None:
        self.source_id = source_id
        self.destination_id = destination_id
        self.next_waypoint_id = next_waypoint_id
        self.last_waypoint_id = last_waypoint_id
        self.data_length = data_length
        self.reversed_flag = reversed_flag
        self.message_type = message_type

    def to_json(self):
        return json.dumps(self.__dict__)

    @classmethod
    def from_json(cls, json_str):
        data = json.loads(json_str)
        return cls(**data)
