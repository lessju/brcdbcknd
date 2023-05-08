class Bin:
    """ Represents a recycling bin """

    def __init__(self, bin_id):
        """ Class constructor """
        self._bin_id = bin_id
        self._available = False
        self._online = False

    def _get_available(self):
        return self._available

    def _set_available(self, value: bool):
        self._available = value

    def _get_online(self):
        return self._online

    def _set_online(self, value: bool):
        self._online = value

    available = property(
        fget=_get_available,
        fset=_set_available,
        doc="Determine whether bin is available or not"
    )

    online = property(
        fget=_get_online,
        fset=_set_online,
        doc="Determine whether bin is online or not"
    )
