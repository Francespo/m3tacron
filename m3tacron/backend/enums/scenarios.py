from enum import Enum

class Scenario(str, Enum):
    ANCIENT_KNOWLEDGE = "ancient_knowledge"
    ASSAULT_AT_THE_SATELLITE_ARRAY = "assault_at_the_satellite_array"
    ASSAULT_THE_SATELLITE_ARRAY = "assault_the_satellite_array"  # Alternate spelling on some sites
    CHANCE_ENGAGEMENT = "chance_engagement"
    SALVAGE_MISSION = "salvage_mission"
    SCRAMBLE_THE_TRANSMISSIONS = "scramble_the_transmissions"

    @property
    def label(self) -> str:
        match self:
            case Scenario.ANCIENT_KNOWLEDGE: return "Ancient Knowledge"
            case Scenario.ASSAULT_AT_THE_SATELLITE_ARRAY: return "Assault at the Satellite Array"
            case Scenario.ASSAULT_THE_SATELLITE_ARRAY: return "Assault the Satellite Array"
            case Scenario.CHANCE_ENGAGEMENT: return "Chance Engagement"
            case Scenario.SALVAGE_MISSION: return "Salvage Mission"
            case Scenario.SCRAMBLE_THE_TRANSMISSIONS: return "Scramble the Transmissions"

    def __str__(self) -> str:
        return self.value
