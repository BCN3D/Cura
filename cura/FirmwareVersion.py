import re #To replace parts of version strings with regex.

class FirmwareVersion(object):
    def __init__(self, version):
        super().__init__()
        self._version = version
        machine_prefix, version_number = version.split("-")
        version_number_list = version_number.split(".")
        revision = re.sub("[A-Za-z]", "", version_number_list[2])
        self._is_prerelease = revision != version_number_list[2]

        try:
            self._machine_prefix = int(machine_prefix)
            self._major = int(version_number_list[0])
            self._minor = int(version_number_list[1])
            self._revision = int(revision)
        except IndexError:
            pass
        except ValueError:
            raise ValueError

    @classmethod
    def isVersion(cls, version):
        return re.match(r'^[0-9]+-[0-9]+\.[0-9]+\.[0-9]+.*$', version) is not None

    def isPrerelease(self):
        return self._is_prerelease

    def getMachinePrefix(self):
        return self._machine_prefix

    def getMajor(self):
        return self._major

    def getMinor(self):
        return self._minor

    def getRevision(self):
        return self._revision

    def __gt__(self, other):
        if isinstance(other, FirmwareVersion):
            return other.__lt__(self)
        elif isinstance(other, str):
            return FirmwareVersion(other).__lt__(self)
        else:
            return False

    def __lt__(self, other):
        if isinstance(other, FirmwareVersion):
            if self._major < other.getMajor():
                return True
            if self._minor < other.getMinor() and self._major == other.getMajor():
                return True
            if self._revision < other.getRevision() and self._major == other.getMajor() and self._minor == other.getMinor():
                return True
            return False
        elif isinstance(other, str):
            return self < FirmwareVersion(other)
        else:
            return False

    def __eq__(self, other):
        if isinstance(other, FirmwareVersion):
            return self._major == other.getMajor() and self._minor == other.getMinor() and self._revision == other.getRevision()
        elif isinstance(other, str):
            return self == FirmwareVersion(other)
        else:
            return False

    def __str__(self):
        return self._version

    def __hash__(self):
        return hash(self.__str__())
