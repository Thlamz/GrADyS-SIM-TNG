from typing import List

from ping import PingProtocol
from simulator.handler.assertion import assert_always_true_for_simulation, AssertionHandler
from simulator.handler.communication import CommunicationHandler
from simulator.handler.mobility import MobilityHandler
from simulator.handler import TimerHandler
from simulator.handler import VisualizationHandler
from simulator.node import Node
from simulator.simulation import SimulationBuilder, SimulationConfiguration


@assert_always_true_for_simulation(name="received_equals_sent")
def assert_received_equals_sent(nodes: List[Node[PingProtocol]]) -> bool:
    received = 0
    sent = 0
    for node in nodes:
        received += node.protocol_encapsulator.protocol.received
        sent += node.protocol_encapsulator.protocol.received
    return received == sent


if __name__ == '__main__':
    builder = SimulationBuilder(SimulationConfiguration(duration=30, debug=True, real_time=True))
    builder.add_handler(CommunicationHandler())
    builder.add_handler(TimerHandler())
    builder.add_handler(MobilityHandler())
    builder.add_handler(VisualizationHandler())
    builder.add_handler(AssertionHandler([assert_received_equals_sent]))

    builder.add_node(PingProtocol, (0, 0, 0))
    builder.add_node(PingProtocol, (1, 1, 0))

    simulation = builder.build()
    simulation.start_simulation()
