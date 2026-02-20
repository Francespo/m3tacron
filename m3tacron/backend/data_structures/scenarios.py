"""
2.5 Scenarios.
"""
from enum import StrEnum

class Scenario(StrEnum):
    ANCIENT_KNOWLEDGE = "ancient_knowledge"
    ASSAULT_AT_THE_SATELLITE_ARRAY = "assault_at_the_satellite_array"
    CHANCE_ENGAGEMENT = "chance_engagement"
    SALVAGE_MISSION = "salvage_mission"
    SCRAMBLE_THE_TRANSMISSIONS = "scramble_the_transmissions"
    NO_SCENARIO = "no_scenario"
    OTHER_UNKNOWN = "other_unknown"

    @property
    def label(self) -> str:
        match self:
            case Scenario.ANCIENT_KNOWLEDGE: return "Ancient Knowledge"
            case Scenario.ASSAULT_AT_THE_SATELLITE_ARRAY: return "Assault at the Satellite Array"
            case Scenario.CHANCE_ENGAGEMENT: return "Chance Engagement"
            case Scenario.SALVAGE_MISSION: return "Salvage Mission"
            case Scenario.SCRAMBLE_THE_TRANSMISSIONS: return "Scramble the Transmissions"
            case Scenario.NO_SCENARIO: return "No Scenario"
            case Scenario.OTHER_UNKNOWN: return "Other/Unknown"

