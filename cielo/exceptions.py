# coding: utf-8

__all__ = ['GetAuthorizedException', 'CaptureException', 'TokenException']

class GetAuthorizedException(Exception):
    def __init__(self, id, message=None):
        self.id = id
        self.message = message

    def __str__(self):
        return u'%s - %s' % (self.id, self.message)


class CaptureException(Exception):
    pass


class TokenException(Exception):
    pass
