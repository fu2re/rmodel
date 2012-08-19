# coding: utf8

from redis.client import Redis
from rmodel.fields.rfield import rfield
from rmodel.fields.rhash import rhash
from rmodel.models.rstore import RStore
from rmodel.models.runit import RUnit
from rmodel.sessions.rsession import RSession
from unittest2.case import TestCase


class ItemModel(RUnit):

    id = rfield(int)
    total = rfield(int)
    hash = rhash(int, 0)


class StoreModel(RStore):

    assign = ItemModel

    prefix = 'store'
    name = rfield(str, 'default_name')


class IndexModel(RUnit):

    prefix = 'model'
    root = True

    lenght = rfield()
    store = StoreModel()


class NewItem(RUnit):

    field = rfield()

    def new(self, value):
        self.field.set(value)


class NewTestModel(RStore):

    root = True
    assign = NewItem


class RModelStoreTest(TestCase):

    def setUp(self):
        self.redis = Redis()
        self.redis.flushdb()
        self.session = RSession()
        self.model = IndexModel(session=self.session)

    def test_init(self):
        self.assertIsInstance(self.model, IndexModel)

    def test_session(self):
        self.assertEqual(self.session, self.model.store._session)

    def test_session_inherit(self):
        self.assertEqual(self.session, self.model.store.add()._session)

    def test_session_override_get(self):
        session = RSession()
        self.model.store.set(1)
        self.assertEqual(session, self.model.store.get(1, session)._session)

    def test_session_override_add_set(self):
        session = RSession()
        self.assertEqual(session,
                         self.model.store.add(session=session)._session)
        self.assertEqual(session,
                         self.model.store.set(2, session=session)._session)

    def test_addModel(self):
        model = IndexModel()
        item = model.store.add()
        self.assertEqual(isinstance(item, ItemModel), True)

        item.id.set(1)
        item.total.set(1)
        data = item.data()

        self.assertEqual(data, {'id': 1, 'hash': {}, 'total': 1})
        self.assertEqual(model.store.keys(), ['1'])
        self.assertEqual(1 in model.store, True)
        self.assertEqual(len(model.store), 1)

        self.assertEqual(model.store.get(1).data(), data)

        self.assertEqual(model.store.new_key(), long(2))
        item = model.store.add()
        self.assertEqual(model.store.new_key(), long(4))
        self.assertEqual(len(model.store), 2)

    def test_data(self):
        model = IndexModel()
        item = model.store.add()
        self.assertEqual(isinstance(item, ItemModel), True)
        item.total.set(2)
        item.id.set(1)

        item2 = model.store.set(2)
        item2.id.set(8)
        item2.total.set(4)
        self.assertEqual(item.id.get(), 1)
        self.assertEqual(item.total.get(), 2)

        self.assertDictEqual(item.data(), {'total': 2, 'hash': {}, 'id': 1})
        self.assertDictEqual(item2.data(), {'total': 4, 'hash': {}, 'id': 8})
        self.assertDictEqual(model.store.data(),
                         {'1': {'hash': {}, 'id': 1, 'total': 2},
                          '2': {'hash': {}, 'id': 8, 'total': 4},
                          'name': 'default_name'})

    def test_remove(self):
        model = IndexModel()
        item = model.store.add()
        item.total = 2
        item.id = 1

        self.assertTrue(model.store.get(1))
        model.store.remove_item(1)
        self.assertFalse(model.store.get(1))

    def test_with_model(self):
        model = StoreModel(inst=None)
        self.assertEqual(model.data(), {'name': 'default_name'})

    def test_two_models(self):
        model = StoreModel(prefix='store1', inst=None)

        item1 = model.set(1)
        item2 = model.set(2)
        item2.hash['1'] = 1

        self.assertDictEqual(item1.data(), {'hash': {}, 'id': None,
                                            'total': None})
        self.assertDictEqual(item2.data(), {'hash': {'1': 1}, 'id': None,
                                            'total': None})

    def test_clean_remove_all(self):
        model = StoreModel(prefix='1', inst=None)
        item = model.set(1)

        self.assertEqual(model.cursor.key, '1')
        self.assertEqual(item.cursor.key, '1:1')

        item.id.set(1)
        item.hash.set('2', '3')
        self.assertEqual(self.redis.hgetall('1:1'), {'id': '1'})
        self.assertEqual(self.redis.hgetall('1:1:hash'), {'2': '3'})
        self.assertEqual(self.redis.hgetall('1:_KEY'), {'1': '_KEY'})

        model.remove()

        self.assertEqual(self.redis.hgetall('1:1'), {})
        self.assertEqual(self.redis.hgetall('1:1:hash'), {})
        self.assertEqual(self.redis.hgetall('1'), {})

    def test_move(self):
        model = StoreModel(prefix='store', inst=None)
        item = model.set(1)
        item.id.set(2)
        self.assertEqual(len(model), 1)

        model.move(item.prefix, 2)
        self.assertEqual(len(model), 1)
        self.assertEqual(model.keys(), ['2'])

    def test_custom_new_with_args(self):
        model = NewTestModel()
        item = model.add(args=('test_values',))
        self.assertEqual(item.field.get(), 'test_values')
        item = model.set('test', args=('somthing_else',))
        self.assertEqual(item.field.get(), 'somthing_else')
