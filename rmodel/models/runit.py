#coding: utf8

from redis.client import Redis
from rmodel.common import Run
from rmodel.cursor import Cursor
from rmodel.fields.base_bound import BaseBound, no_changes, no_session


class RUnit(BaseBound):

    defaults = False

    redis = Redis()
    prefix = ''

    @classmethod
    def fields_gen(cls):
        for name in dir(cls):
            field = getattr(cls, name)
            if hasattr(field, '__unbound__'):
                yield name, field

    @Run('init')
    def __init__(self, prefix=None, inst=None, session=no_session):
        self._session = session
        self.class_fields = dict(self.fields_gen())
        if prefix is not None:
            self.prefix = str(prefix)

        if inst is not None:
            self.cursor = inst.cursor.new(self.prefix)
        else:
            self.cursor = Cursor(self.prefix)

        self._fields = tuple(self.init_fields())
        self.instance = inst

    def init_fields(self):
        for name, field in self.class_fields.items():
            yield field.bound(self, name)

    def fields(self):
        return self._fields

    def typer(self, value):
        return value

    def process_data(self, values):
        result = {}
        for field in self.fields():
            result[field.prefix] = field.process_data(values)
        return result

    def remove(self):
        pipe = self.redis.pipeline()
        self.clean(pipe, self)
        pipe.execute()

    def changes_gen(self):
        for field in self.fields():
            changes = field.changes()
            if changes is not no_changes:
                yield field.prefix, changes

    def changes(self):
        return dict(self.changes_gen()) or no_changes

    def clean(self, pipe, inst):
        for field in self.fields():
            field.clean(pipe, self)

    def data(self, pipe=None, key=None):
        child = True

        if not pipe:
            child = False
            pipe = self.redis.pipeline()

        for field in self.fields():
            field.data(pipe, key=self.cursor.key)

        if not child:
            values = map(self.typer, pipe.execute())
            return self.process_data(values)

    def incr(self, sect, key, val=1):
        section = getattr(self, sect)
        if not section.get(key):
            section[key] = val
        else:
            section[key] += val

    def decr(self, sect, key, val=1):
        section = getattr(self, sect)
        section[key] -= val
        if not section.get(key):
            section.remove(key)

    def new(self):
        pass

    def init(self):
        pass
