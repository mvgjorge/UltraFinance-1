#!/usr/bin/env python
# -*- coding: utf-8 -*-


class SQLUtil(object):
    """
    Class that includes:
    1) how to build connection with database with mysqlalchemy
    2) query information from db
    3) other tools
    """

    def __init__(self, engine):
        """
        Create connection and other essential stuff
        :param engine:
        :return:
        """
        from sqlalchemy import MetaData
        self.engine = engine
        self.metadata = MetaData(self.engine)
        self.conn = self.engine.connect()

    def list_table_in_db(self):
        """
        Function that shows all the tables in the database
        :param engine: sqlalchemy engine
        :return:
        """
        from sqlalchemy import inspect
        inspector = inspect(self.engine)
        return inspector.get_table_names()

    def check_table_list_avail(self, table_list):
        """
        Function that checks if the stock_list exist
        :param stock_list: stock name list
        :return: dict of bool value
        """
        if isinstance(table_list, str):
            table_list = (table_list, )
        if not isinstance(table_list, (list, tuple)):
            raise ValueError('Input arg not correct: stock_list should be a tuple or list')

        bool_dict = {}
        db_table_list = self.list_table_in_db()
        for ticket in table_list:
            if ticket in db_table_list:
                bool_dict[ticket] = True
            else:
                bool_dict[ticket] = False
        return bool_dict

    def check_one_table_avail(self, table_name):
        """
        Function that checks if a specific stock exists
        """
        if not isinstance(table_name, str):
            raise ValueError('Input arg is not correct')
        db_table_list = self.list_table_in_db()
        bool_value = table_name in db_table_list
        return bool_value

    @staticmethod
    def _map_class_to_some_table_(cls, table, entity_name, **kw):
        """
        Map the table to class
        :param cls: class template
        :param table: table instance in SQLAlchemy
        :param entity_name: table in the database
        :param kw:
        :return: class mapped to the table
        """
        from sqlalchemy.orm import mapper
        newcls = type(entity_name, (cls, ), {})
        mapper(newcls, table, **kw)
        return newcls

    def create_session(self):
        """
        Create Session in the SQLAlchemy. Query will be based on Session.
        :return: SQLAlchemy session
        """
        from sqlalchemy.orm import sessionmaker
        session = sessionmaker(bind=self.engine)
        session = session()
        return session

    def finalize(self):
        """
        Finalize the connection to the database, which should be called every time when all the work are finished.
        :return:
        """
        self.engine.dispose()

    @staticmethod
    def finalize_session(session):
        """
        Finalize SQLAlchemy session
        :param session:
        :return:
        """
        session.close()