class ZkillFetchError(Exception):
    """Raised when an error occurs fetch data from zkill API"""

class HydrationException(Exception):
    """Base Exception for all Hydration Errors"""

class KillmailHydrationException(HydrationException):
    """An error occured hydrating a character"""

class CharacterHydrationException(HydrationException):
    """An error occured hydrating a killmail"""

class CorporationHydrationException(HydrationException):
    """An error occured hydrating a corporation"""

class AllianceHydrationException(HydrationException):
    """An error occured hydrating an alliance"""

class TypePriceHydrationException(HydrationException):
    """An error occured hydrating type prices"""