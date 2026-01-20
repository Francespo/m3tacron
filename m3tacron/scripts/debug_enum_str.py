from m3tacron.backend.enums.platforms import Platform
from m3tacron.backend.enums.scenarios import Scenario

def run():
    p = Platform.ROLLBETTER
    print(f"Platform: {p}")
    print(f"Platform.value: {p.value}")
    print(f"str(Platform): {str(p)}")
    print(f"type: {type(p)}")
    
    s = Scenario.CHANCE_ENGAGEMENT
    print(f"Scenario: {s}")
    print(f"str(Scenario): {str(s)}")

if __name__ == "__main__":
    run()
