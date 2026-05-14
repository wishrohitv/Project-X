from datetime import UTC

from modules import datetime


class CDateTime:
    @property
    def timeStamp(self):
        return datetime.now().timestamp()

    @property
    def fullYear(self):
        return datetime.now().year
