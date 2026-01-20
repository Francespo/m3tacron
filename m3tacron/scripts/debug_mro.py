from m3tacron.backend.enums.platforms import Platform

def run():
    print(f"MRO: {Platform.mro()}")
    p = Platform.ROLLBETTER
    print(f"Value: '{p}'")
    print(f"Str func: {Platform.__str__}")
    
    # Check what 'str' mixin provides
    class JustStrEnum(str, Platform.__base__.__bases__[1]): # Hacky way to try to reproduce raw Enum
        pass
        
    # Let's just create a raw one to compare without my fix
    from enum import Enum
    class RawEnum(str, Enum):
        TEST = "test"
        
    print(f"RawEnum MRO: {RawEnum.mro()}")
    print(f"RawEnum.TEST: {RawEnum.TEST}")
    print(f"str(RawEnum.TEST): {str(RawEnum.TEST)}")

if __name__ == "__main__":
    run()
