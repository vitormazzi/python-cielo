# coding: utf-8

__all__ = ['CieloException', 'GetAuthorizedException', 'CaptureException', 'TokenException']

class CieloException(Exception):
    def __init__(self, id, message=None, raw_data=None):
        self.id = id
        self.message = message
        self.raw_data = None

    def __repr__(self):
        if self.raw_data:
            return u'%s - %s (%s)' % (self.id, self.message, self.raw_data)
        else:
            return u'%s - %s' % (self.id, self.message)

class GetAuthorizedException(CieloException):
    pass


class CaptureException(Exception):
    pass


class TokenException(Exception):
    pass
