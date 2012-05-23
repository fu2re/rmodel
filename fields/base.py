# coding: utf8

def nullfunct(self, inst, data):
    return data

class RProperty(object):

    redis_field = True

    def __init__(self, _type=str, default=None, prefix=None):

        self._default = default
        self.prefix = prefix
        self.type = _type

    def assign(self, inst):
        self.cursor = inst.cursor.new(self.prefix)
        self.key = self.cursor.key
        self.instance = inst
        self.redis = inst.redis

    def typer(self, value):
        if value != None:
            if self.type:
                value = self.type(value)
        return value

    def process_result(self, rt):
        if not rt is None:
            return self.type(rt)
        else:
            return self.default

    def data(self, redis, key):
        return redis.hget(key, self.prefix)

    @property
    def _setting(self):
        return (self.prefix, self._default)

    @property
    def default(self):
        if not self._default is None:
            return self._default
        elif self.instance.defaults:
            return self.instance.defaults.get(self.prefix)