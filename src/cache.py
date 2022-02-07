import threading
from custom_types import response

# TODO replace the current organization based on a list by an organization based on a dict (would be more efficient)
__caches = []


class __Elem:
    """ Wrapper for an element in the cache, containing the element in cache, the id of the owner
     of this element and a Timer object which trigger the removal of the element from the cache when over """

    def __init__(self, page, owner, lifetime):
        self.page = page
        self.owner = owner
        self.life = threading.Timer(lifetime * 60, self.die)
        self.life.start()

    def die(self):
        if self.life.is_alive():
            self.life.cancel()
        _remove(self)

    def new_lifetime(self, new_lifetime):
        self.life.cancel()
        self.life = threading.Timer(new_lifetime * 60, self.die)
        self.life.start()


def put_in_cache(session, owner, lifetime: int = 5):
    previous_cache = _get_cache_wrapper(owner)
    if previous_cache is not None:  # remove the older cache before adding a new one
        _remove(previous_cache)
    __caches.append(__Elem(session, owner, lifetime))


def _remove(to_remove) -> None:
    to_remove.life.cancel()
    __caches.remove(to_remove)


def has_cache(user) -> bool:
    return any(user.discord_id == elem.owner.discord_id for elem in __caches)


def get_cache(user) -> response:
    return next((elem.page for elem in __caches if user.discord_id == elem.owner.discord_id), None)


def _get_cache_wrapper(user) -> __Elem:
    return next((elem for elem in __caches if user.discord_id == elem.owner.discord_id), None)
