"""
Upgrade types for X-Wing.
"""
from enum import StrEnum

class UpgradeType(StrEnum):
    Astromech = "astromech"
    Cannon = "cannon"
    Cargo = "cargo"
    Command = "command"
    Configuration = "configuration"
    Crew = "crew"
    Device = "device"
    ForcePower = "force_power"
    Gunner = "gunner"
    Hyperspace = "hyperspace"
    Hardpoint = "hardpoint"
    Hyperdrive = "hyperdrive"
    Illicit = "illicit"
    Missile = "missile"
    Modification = "modification"
    Sensor = "sensor"
    TacticalRelay = "tactical_relay"
    Talent = "talent"
    Team = "team"
    Tech = "tech"
    Title = "title"
    Turret = "turret"

    @property
    def label(self) -> str:
        match self:
            case UpgradeType.Astromech: return "Astromech"
            case UpgradeType.Cannon: return "Cannon"
            case UpgradeType.Cargo: return "Cargo"
            case UpgradeType.Command: return "Command"
            case UpgradeType.Configuration: return "Configuration"
            case UpgradeType.Crew: return "Crew"
            case UpgradeType.Device: return "Device"
            case UpgradeType.ForcePower: return "Force Power"
            case UpgradeType.Gunner: return "Gunner"
            case UpgradeType.Hyperspace: return "Hyperspace"
            case UpgradeType.Hardpoint: return "Hardpoint"
            case UpgradeType.Hyperdrive: return "Hyperdrive"
            case UpgradeType.Illicit: return "Illicit"
            case UpgradeType.Missile: return "Missile"
            case UpgradeType.Modification: return "Modification"
            case UpgradeType.Sensor: return "Sensor"
            case UpgradeType.TacticalRelay: return "Tactical Relay"
            case UpgradeType.Talent: return "Talent"
            case UpgradeType.Team: return "Team"
            case UpgradeType.Tech: return "Tech"
            case UpgradeType.Title: return "Title"
            case UpgradeType.Turret: return "Turret"

    def __str__(self) -> str:
        return self.value
