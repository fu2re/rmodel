#coding: utf8

from model.rmodel import RModel
from model.fields.rfield import rfield
from model.fields.rhash import rhash
import timeit

class TestBuilding(RModel):

    prefix = 'tbuilding'

    profit = rfield("profit")
    build_total = rfield("build_total")
    build_one = rfield("build_one")
    lock = rfield("lock")
    public = rfield("public")
    id = rfield("id")
    flash = rhash("flash")

code = '''
t = TestBuilding()

t.data()

'''
decode = '''

coder.decode('test')
'''

if __name__ == '__main__':
    timer = timeit.Timer(code, 'from __main__ import TestBuilding')
#    timer_all = timeit.Timer(code + decode, 'from dict_to_redis import DictToRedis')
    print 5000, 'encodings', timer.timeit(5000)
#    print 5000, 'encodings+decode', timer_all.timeit(5000)

