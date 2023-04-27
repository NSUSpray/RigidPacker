import sqlite3
from math import pi
from dataclasses import dataclass, field


@dataclass
class _PhysicalItemDataMixin:
    self_mass: float = field(default=1.0, init=False)
    self_volume: float = field(default=4/3*pi*(0.1)**3, init=False)


@dataclass
class ItemData(_PhysicalItemDataMixin):

    ''' Represents data transfer objects (DTO). Contains only database data '''

    id: int
    name: str
    product_name: str = ''
    is_root: bool = field(init=False)

    def __post_init__(self):
        self.is_root = (self.id==Repository.root_id)

    def __hash__(self): return self.id

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.id == other.id


class Repository:

    ''' Represents data access object (DAO) '''

    default_arrangement = 'current'
    root_id = 0
    root_name = 'root'

    def __init__(self, filename):
        self.__connect = sqlite3.connect(filename)
        self.__cursor = self.__connect.cursor()
        self.__arrangement_id: int
        self._root = ItemData(self.root_id, self.root_name)
        self.arrangement = self.default_arrangement

    def __del__(self):
        self.__cursor.close()
        self.__connect.close()

    @property
    def arrangement(self):
        request = '''
            SELECT name FROM arrangement WHERE arrangement_id IS ?
            '''
        data = (self.__arrangement_id,)
        self.__cursor.execute(request, data)
        response = self.__cursor.fetchone()
        if response: return response[0]

    @arrangement.setter
    def arrangement(self, name):
        request = '''
            SELECT arrangement_id FROM arrangement WHERE name IS ?
            '''
        data = (name,)
        self.__cursor.execute(request, data)
        response = self.__cursor.fetchone()
        if not response: raise ValueError
        self.__arrangement_id = response[0]

    def children_of(self, item):
        request = '''
            SELECT item_id, name, product_name
            FROM placement LEFT JOIN item USING(item_id)
            WHERE parent_id IS ? AND arrangement_id IS ?
            '''
        data = (item.id or None, self.__arrangement_id)
        self.__cursor.execute(request, data)
        response = self.__cursor.fetchall()
        return [ItemData(*fields) for fields in response]

    def shift(self, items, parent):
        request = '''
            UPDATE placement SET parent_id = ?
            WHERE item_id IN (%s) AND arrangement_id IS ?
            ''' % ','.join('?' * len(items))
        item_ids = [item.id for item in items]
        data = (parent.id or None, *item_ids, self.__arrangement_id)
        self.__cursor.execute(request, data)
        self.__connect.commit()
