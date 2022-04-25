import threading
from src.custom_types import response

# keys : user.discord_id
# values : __Elem
__caches = dict()


class __Elem:
    """
    Wrapper for an element in the cache, containing the element in cache, the id of the owner
    of this element and a Timer object which trigger the removal of the element from the cache when over
    """

    def __init__(self, page, owner, lifetime):
        self.page = page
        self.owner = owner
        self.life = threading.Timer(lifetime * 60, self.die)
        self.life.start()

    def die(self):
        remove_cache(self.owner)

    def new_lifetime(self, new_lifetime):
        self.life.cancel()
        self.life = threading.Timer(new_lifetime * 60, self.die)
        self.life.start()


def put_in_cache(session, owner, lifetime: int = 5) -> None:
    if has_cache(owner):
        print('yo')
        __caches[owner.discord_id].life.cancel()
    __caches[owner.discord_id] = __Elem(session, owner, lifetime)


def remove_cache(owner) -> response | None:
    c = __caches.get(owner.discord_id)
    if c is None:
        return None
    c.life.cancel()
    return __caches.pop(owner.discord_id).page


def has_cache(user) -> bool:
    return __caches.get(user.discord_id) is not None


def get_cache(user) -> response | None:
    res = __caches.get(user.discord_id)
    if res is not None:
        return res.page
    return None


def _get_cache_wrapper(user) -> __Elem:
    return __caches.get(user.discord_id)
