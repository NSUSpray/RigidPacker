import sqlite3


class ItemBase:

    ''' Represents data transfer objects (DTO). Contains only database data '''

    def __init__(self, item_id, name, product_name=''):
        self.id = item_id
        self.name = name
        self.product_name = product_name

    @property
    def is_root(self): return self.id == Storage.root_id


class Storage:

    ''' Represents data access object (DAO) '''

    default_arrangement = 'current'
    root_id = 0
    root_name = 'root'

    def __init__(self, filename):
        self._connect = sqlite3.connect(filename)
        self._cursor = self._connect.cursor()
        self.arrangement = self.default_arrangement
        self.root = ItemBase(self.root_id, self.root_name)

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

    def item(self, name):
        self._cursor.execute('''
            SELECT item_id, name, product_name FROM item WHERE name IS ?
            ''', (name,))
        response = self._cursor.fetchone()
        if not response: raise sqlite3.ProgrammingError
        data = response[0]
        return ItemBase(data[0], data[1])

    def children_of(self, item):
        self._cursor.execute('''
            SELECT item_id, name, product_name FROM placement
            LEFT JOIN item USING(item_id)
            WHERE parent_id IS ?
            AND arrangement_id IS ?
        ''', (item.id or None, self._arrangement_id))
        response = self._cursor.fetchall()
        return [
            ItemBase(item_id, name, product_name)
                for item_id, name, product_name in response
            ]
