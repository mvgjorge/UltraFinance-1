#!
# -*- coding: utf-8 -*-

import pandas.io.data as web
import datetime
import pandas.io
# import MySQLdb
# build up connection with mysql
import sqlalchemy

from sqlalchemy_stubs import *

class StockOnline(object):
    """
    Class Server includes methods that pull data from online resource and store them into database
    """
    def __init__(self, source='yahoo'):
        self.source=source
        if not(self.__validate_source_connection__()):
            raise RuntimeError("Source Not Valid %s" % self.source)

    def __validate_source_connection__(self):
        test_stock='AAPL'
        # set start and end time
        start = datetime.datetime(2012, 1, 1)
        end = datetime.datetime(2012, 1, 27)
        try:
            web.DataReader(test_stock, self.source, start, end)
            return True
        except:
            return False

    def pull_data(self, stock_list, start=datetime.datetime(2012,1,1), end=datetime.datetime(2013,1,1)):
        """
        Function that pulls data from online resource
        :param stock_list: tuple that stores the name list of stocks
        :param start: start time
        :param end: end time
        :return:
        """
        # check start and end
        if start > end:
            raise ValueError("StartTime is larger than EndTime")

        #print "\n+++++++++++++++++\nPull Data Service"
        stock_table = {}
        for stock in stock_list:
            print "Pull Stock : %s ..." % stock
            try:
                stock_table[stock] = web.DataReader(stock, self.source, start, end)
            except:
                stock_table[stock] = None
                raise RuntimeError("Can't not download Stock: %s" % stock)

        return stock_table

class StockServer(object):

    def __init__(self, username, password, database, host="localhost", dialect="mysql",
                 driver="mysqldb", port="3306"):
        # a sqlalchemy engine connection URL could be constructed as:
        # dialect+driver://username:password@host:port/database
        # engine = sqlalchemy.create_engine('mysql://root:000539@localhost:3306/test')

        db_connection_string = dialect + '+' + driver + '://' + username + ":" + \
            password + "@" + host + ":" + port + "/" + database
        try:
            self.engine = sqlalchemy.create_engine(db_connection_string)
        except:
            raise RuntimeError("Can not create engine for URL: %s" % db_connection_string)

    def finalize_engine(self):
        self.engine.dispose()

    def init_db(self, stock_table, init_mode='fail'):
        """
        Function that init all the stock data(pandas DataFrame)into sql
        :param engine: sqlalchemy engine
        :param init_mode: to_sql if_exist variable
        :return:
        """
        print "\n++++++++++++++++\nInit DB Service"
        for stock_name, stock_data in stock_table.iteritems():
            print "Init Table Name in db: %s" %stock_name
            if stock_data is None:
                print "Data is None...Skip it"
            else:
                # check if table exists
                table_exist=pandas.io.sql.has_table(stock_name, self.engine)
                print "\tTable exist: %s" % table_exist
                table_exist = False
                if not table_exist:
                    try:
                        stock_data.to_sql(stock_name, self.engine, if_exists=init_mode)
                        print "\tCreate table in database... %s" % stock_name
                        # print data
                    except:
                        raise RuntimeError("Can not init table in database for stock %s" %stock_name)

    def get_largest_date(self, stock_name):
        from sqlalchemy.sql import func
        session, stockobj = loadsession(stock_name, self.engine)
        qry = session.query(func.max(stockobj.Date).label("max_date"))
        res = qry.one()
        return res.max_date

    def update_db(self, stock_list):
        """
        Function that updates the database to current date
        :param engine:
        :return:
        """
        print "\n++++++++++++++++++\nUpdate Table Service"

        onlinedata = StockOnline()

        for stock_name in stock_list:
            print "Update table: %s" %stock_name
            table_exist = pandas.io.sql.has_table(stock_name, self.engine)
            print "Table exist: %s" % table_exist
            if table_exist:
                print "Update now..."
                # get end time
                endtime = get_cur_date()
                print type(endtime), endtime
                # get start time
                starttime = self.get_largest_date(stock_name) + datetime.timedelta(days=1)
                print type(starttime), starttime
                stock_table = onlinedata.pull_data((stock_name,), starttime, endtime)
                # write into db
                if stock_table[stock_name] is not None:
                    print "Online Data is not None. Updating..."
                    stock_table[stock_name].to_sql(stock_name, self.engine, if_exists='append')
                else:
                    print "Online Data is None. Skip it..."
            else:
                "Skip this stock"


class StockClient(object):
    """
    Class Client includes method that read all kinds of data from the existing database
    """
    def __init__(self, username, password, database, host="localhost", dialect="mysql",
                 driver="mysqldb", port="3306"):
        # a sqlalchemy engine connection URL could be constructed as:
        # dialect+driver://username:password@host:port/database
        # engine = sqlalchemy.create_engine('mysql://root:000539@localhost:3306/test')

        db_connection_string = dialect + '+' + driver + '://' + username + ":" + \
            password + "@" + host + ":" + port + "/" + database
        try:
            self.engine = sqlalchemy.create_engine(db_connection_string)
        except:
            raise RuntimeError("Can not create engine for URL: %s" % db_connection_string)

    def finalize_engine(self):
        self.engine.dispose()

    def read_full_stock_record(self, stock_list):
        """
        Function that pulls the
        :param stock_list: tuple that stores the stock list
        :return:
        """
        stock_table={}
        boolen_dict = self.check_stock_avail(stock_list)
        for stock in stock_list:
            if boolen_dict[stock]:
                stock_table[stock] = pandas.io.sql.read_sql(stock, self.engine)
            else:
                stock_table[stock] = None
        return stock_table

    def read_stock_record(self, stock_list, starttime, endtime):

        if starttime > endtime:
            raise ValueError('Starttime is larger than endtime')

        for stock_name in stock_list:
            session, stockobj = loadsession(stock_name, self.engine)
            #for key in stockobj.__table__.columns:
            #    print key
            from sqlalchemy import inspect, and_
            inspector = inspect(stockobj)
            #for column in inspector.attrs:
            #    print column.key
            qry = (session.query(stockobj).filter(and_(stockobj.Date >= starttime, stockobj.Date <= endtime)))
            # print qry.first()
        return self.convert_qry_to_DF(qry)

    @staticmethod
    def convert_qry_to_DF(qry):
        stock_table = {}
        index_list = []
        stock_table['Open']=[]
        stock_table['High']=[]
        stock_table['Low']=[]
        stock_table['Close']=[]
        stock_table['Volume']=[]
        stock_table['Adj Close']=[]
        for idx, entry in enumerate(qry.all()):
            print idx, entry.__dict__['Adj Close']
            stock_table['Open'].append(entry.Open)
            stock_table['High'].append(entry.High)
            stock_table['Low'].append(entry.Low)
            stock_table['Close'].append(entry.Close)
            stock_table['Volume'].append(entry.Volume)
            stock_table['Adj Close'].append(entry.__dict__['Adj Close'])
            index_list.append(entry.Date)

        #convert to DataFrame
        df=pandas.DataFrame(stock_table, index=index_list)
        df.index.name = 'Date'
        return df

    def list_stock_in_db(self):
        """
        Function that shows all the stock in the database
        :param engine: sqlalchemy engine
        :return:
        """
        from sqlalchemy import inspect
        inspector = inspect(self.engine)

        return inspector.get_table_names()

    def check_stock_avail(self, stock_list):

        boolen_dict = {}
        db_stock_list = self.list_stock_in_db()
        for stock in stock_list:
            if stock in db_stock_list:
                boolen_dict[stock] = True
            else:
                boolen_dict[stock] = False
        return boolen_dict


def get_cur_date():
    now = datetime.datetime.now()
    return datetime.datetime(now.year, now.month, now.day)