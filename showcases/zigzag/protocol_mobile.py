import logging
import random
from gradysim.protocol.addons.mission_mobility import (
    LoopMission,
    MissionMobilityAddon,
    MissionMobilityConfiguration,
)
from gradysim.protocol.messages.communication import BroadcastMessageCommand, SendMessageCommand
from gradysim.protocol.messages.mobility import GotoCoordsMobilityCommand

from gradysim.protocol.messages.telemetry import Telemetry
from gradysim.protocol.interface import IProtocol
from message import ZigZagMessage, ZigZagMessageType
from utils import CommunicationStatus
from gradysim.simulator.log import SIMULATION_LOGGER


class ZigZagProtocolMobile(IProtocol):
    def __init__(self):
        self.timeout_end: int = 0
        self.timeout_set: bool = False
        self.timeout_duration: int = 5
        self.communication_status: CommunicationStatus = CommunicationStatus.FREE
        self.tentative_target: int = -1
        self.last_target: int = -1
        self.current_data_load: int = 0
        self.stable_data_load: int = self.current_data_load
        self.current_telemetry: Telemetry
        self.last_stable_telemetry: Telemetry
        self.last_payload: ZigZagMessage = ZigZagMessage()
        self._logger = logging.getLogger(SIMULATION_LOGGER)

    def initialize(self):
        self.provider.tracked_variables["current_data_load"] = self.current_data_load

        self.mission: MissionMobilityAddon = MissionMobilityAddon(
            self, MissionMobilityConfiguration(loop_mission=LoopMission.REVERSE)
        )

        self.mission.start_mission([(150, 150, 5), (150, -150, 5), (-150, -150, 5), (-150, 150, 5)])

        # self._update_payload()
        self.provider.schedule_timer("", self.provider.current_time() + random.random())

    def handle_timer(self, timer: str):
        self._send_heartbeat()        
        self.provider.schedule_timer("", self.provider.current_time() + random.random())

    def handle_packet(self, message: str):
        message: ZigZagMessage = ZigZagMessage.from_json(message)

        match message.message_type:
            case ZigZagMessageType.HEARTBEAT:
                if not self._is_timedout():
                    self._reset_parameters()
                    self.tentative_target = message.source_id
                    self._send_message()

            case ZigZagMessageType.PAIR_REQUEST:
                if self._is_timedout() or message.destination_id != self.provider.get_id():
                    return
                else: 
                    if self.communication_status != CommunicationStatus.PAIRED:
                        self.tentative_target = message.source_id
                        self.communication_status = CommunicationStatus.PAIRED
                        self._send_message()

            case ZigZagMessageType.PAIR_CONFIRM:
                if self._is_timedout() or message.destination_id != self.provider.get_id():
                    return 
                else:
                    if message.source_id == self.tentative_target:
                        if self.communication_status != CommunicationStatus.PAIRED_FINISHED:
                            self._initiate_timeout() 

                            # if self.mission.is_reversed == message.reversed_flag: 
                            if self.mission.is_reversed != message.reversed_flag or self.provider.get_id() > message.source_id:
                                print("test5")
                                reversed = not self.mission.is_reversed
                                self.mission.set_reversed(reversed)

                                self.communication_status = CommunicationStatus.PAIRED_FINISHED

                                self._send_message()

            case ZigZagMessageType.BEARER:
                # Only used to exchange information between drone and sensor
                self.current_data_load = self.current_data_load + message.data_length
                self.stable_data_load = self.current_data_load
                self.provider.tracked_variables["current_data_load"] = self.current_data_load

        # self._update_payload()

    def _send_message(self):
        message = ZigZagMessage(
            source_id=self.provider.get_id(),
            reversed_flag=self.mission.is_reversed,
        )

        if self.provider.get_id() == self.tentative_target:
            return

        match self.communication_status:
            case CommunicationStatus.FREE:
                message.message_type = ZigZagMessageType.PAIR_REQUEST
                message.destination_id = self.tentative_target

            case CommunicationStatus.PAIRED | CommunicationStatus.PAIRED_FINISHED:
                message.message_type = ZigZagMessageType.PAIR_CONFIRM
                message.destination_id = self.tentative_target
                message.data_length = self.stable_data_load

        self.last_payload = message

        if self.tentative_target < 0:
            command = BroadcastMessageCommand(
                message=message.to_json()
            )

        else:
            command = SendMessageCommand(
                message=message.to_json(), destination=self.tentative_target
            )

        self.provider.send_communication_command(command)

    def handle_telemetry(self, telemetry: Telemetry):
        self.current_telemetry = telemetry

        if self._is_timedout():
            self.last_stable_telemetry = telemetry

    def finish(self):
        pass

    def _send_heartbeat(self):
        message = ZigZagMessage(
            source_id=self.provider.get_id(),
            reversed_flag=self.mission.is_reversed,
            message_type=ZigZagMessageType.HEARTBEAT
        )

        command = BroadcastMessageCommand(
            message=message.to_json()
        )
        self.provider.send_communication_command(command)

    def _initiate_timeout(self):
        if self.timeout_duration > 0:
            self.timeout_end = self.provider.current_time() + self.timeout_duration
            self.timeout_set = True

    def _is_timedout(self):
        def __is_timedout():
            if self.timeout_set:
                if self.provider.current_time() < self.timeout_end:
                    return True
                else:
                    self.timeout_set = False
                    return False
            else:
                return False
        old_timeout_set = self.timeout_set
        is_timedout = __is_timedout()
        if not is_timedout and old_timeout_set:
            self._reset_parameters()
        return is_timedout

           
    def _reset_parameters(self):
        self.timeout_set = False
        self.last_target = self.tentative_target
        self.tentative_target = -1
        self.communication_status = CommunicationStatus.FREE
        self.last_stable_telemetry = self.current_telemetry
        self.stable_data_load = self.current_data_load
