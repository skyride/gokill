
class HydrationException(Exception):
    """Base Exception for all Hydration Errors"""

class KillmailHydrationException(Exception):
    """An error occured hydrating a character"""

class CharacterHydrationException(Exception):
    """An error occured hydrating a killmail"""

class CorporationHydrationException(Exception):
    """An error occured hydrating a corporation"""

class AllianceHydrationException(Exception):
    """An error occured hydrating an alliance"""