import sqlite3
from math import pi
from dataclasses import dataclass, field


@dataclass
class _ItemDataBase:
    id: int
    name: str
    product_name: str = ''
    is_root: bool = field(init=False)
    def __post_init__(self): self.is_root = (self.id==Storage.root_id)


@dataclass
class _PhysicalItemDataMixin:
    self_mass: float = 1.0
    self_volume: float = 4/3*pi * (0.1)**3


@dataclass
class ItemData(_PhysicalItemDataMixin, _ItemDataBase):
    ''' Represents data transfer objects (DTO). Contains only database data '''


class Storage:

    ''' Represents data access object (DAO) '''

    default_arrangement = 'current'
    root_id = 0
    root_name = 'root'

    def __init__(self, filename):
        self._connect = sqlite3.connect(filename)
        self._cursor = self._connect.cursor()
        self._arrangement_id: int
        self.arrangement = self.default_arrangement
        self.root = ItemData(self.root_id, self.root_name)

    def __del__(self):
        self._cursor.close()
        self._connect.close()

    @property
    def arrangement(self):
        self._cursor.execute('''
            SELECT name FROM arrangement WHERE arrangement_id IS ?
            ''', (self._arrangement_id,))
        response = self._cursor.fetchone()
        if response: return response[0]

    @arrangement.setter
    def arrangement(self, name):
        self._cursor.execute('''
            SELECT arrangement_id FROM arrangement WHERE name IS ?
            ''', (name,))
        response = self._cursor.fetchone()
        if not response: raise sqlite3.ProgrammingError
        self._arrangement_id = response[0]

    def children_of(self, item):
        self._cursor.execute('''
            SELECT item_id, name, product_name FROM placement
            LEFT JOIN item USING(item_id)
            WHERE parent_id IS ?
            AND arrangement_id IS ?
        ''', (item.id or None, self._arrangement_id))
        response = self._cursor.fetchall()
        return [ItemData(*fields) for fields in response]
