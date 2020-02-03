# CEM - Cluster Elasticity Manager 
# Copyright (C) 2011 - GRyCAP - Universitat Politecnica de Valencia
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import sqlite3 
import logging
import sys
import time



class DataBase:
    RETRY_SLEEP = 2
    MAX_RETRIES = 15
    LOG = logging.getLogger('DB')

    def __init__(self, db_file):
        self.db_file = db_file
        self.connection = None
        
    def connect(self):
        retries_cont = 1
        while retries_cont < self.MAX_RETRIES:
            try:
                DataBase.LOG.debug('Connecting ... ('+ str(retries_cont) +'/' + str(self.MAX_RETRIES) +')')
                self.connection = sqlite3.connect(self.db_file)
                DataBase.LOG.debug('Connection created successfully')
                return True
            except (ValueError):
                DataBase.LOG.warn('Cannot connect with ' + self.db_file + ': ' + ValueError)                
            retries_cont += 1
            time.sleep(self.RETRY_SLEEP)
        DataBase.LOG.error('Maximum number of retries reached. Cannot connect with ' + self.db_file )
        return False

    def execute(self, sql, args=None, fetch=True):
        """ Executes a SQL sentence that returns results
            Arguments:
            - sql: The SQL sentence
            - args: A List of arguments to substitute in the SQL sentence
                    (Optional, default None)
            Returns: A list with the "Fetch" of the results
        """
        return self._execute(sql, args, fetch)

    def check_connection_ok (self):
        return not self.connection is None

    def close (self):
        if self.connection is None:
            return False
        else:
            try:
                self.connection.close()
                DataBase.LOG.debug('Connection closed successfully')
                return True
            except (ValueError):
                DataBase.LOG.error('Cannot close connection with ' + self.db_file + ': ' + ValueError)
                return False
            except:
                DataBase.LOG.error('Some error closing the connection')

    def insert (self,args):
        if self.check_connection_ok ():
            sql = ''' INSERT INTO allocation(vmID,name, available)
                VALUES(?,?,?) '''
            cur = self.connection.cursor()
            cur.execute(sql, args)
            self.connection.commit()
            return cur.lastrowid

    def table_exists(self, table):
        sql = 'SELECT name from sqlite_master where type="table" and name="' + table + '"'
        res = None
        if self.connect():
            res = self.execute(sql)
            self.close()
        if len(res) !=0:
            return True
        return False

    def select (self, cols, table, where=None):
        sql = 'SELECT '+ cols + ' FROM '+table
        if where:
            sql += ' WHERE ' + where
        return self.execute(sql)

    def update (self, table, set_tuple_list, where=None):
        sql = ''' UPDATE ''' + table + " SET "
        set_count = 0
        for e in set_tuple_list:
            sql += e[0] + ' = ' + str(e[1])
            if set_count < (len(set_tuple_list)-1):
                sql += ','
            set_count += 1

        if where:
            sql += ' WHERE ' + where
        return self.execute(sql, fetch=False)

    def _execute (self, sql, args, fetch=False):
        if self.check_connection_ok ():
            DataBase.LOG.debug('sql = ' + sql)
            retries_cont = 1
            while retries_cont < self.MAX_RETRIES:
                try:
                    cursor = self.connection.cursor()
                    if args is not None:
                        #new_sql = sql.replace("?", "%s")
                        #DataBase.LOG.debug('new_sql = '+new_sql)
                        cursor.execute(sql, args)
                        #DataBase.LOG.debug('SQL completed')
                    else:
                        cursor.execute(sql)

                    if fetch == True:
                        res = list(cursor.fetchall())
                        #DataBase.LOG.debug( 'Result: ' + str(res))
                    else:
                        self.connection.commit()
                        res = True
                        #DataBase.LOG.debug('Commit finished')

                    return res
                # If the operational error is db lock, retry
                except sqlite3.OperationalError as ex:
                    if str(ex).lower() == 'database is locked':
                        DataBase.LOG.error(ex + 'Reconnecting...')
                        retries_cont += 1
                        self.close() # release the connection
                        time.sleep(self.RETRY_SLEEP)
                        self.connect() # and get it again
                    else:
                        DataBase.LOG.error (ex)
                except (ValueError):
                    DataBase.LOG.error (ValueError)
                retries_cont += 1

        else:
            DataBase.LOG.error('There is not connection. Trying to reconnect....')
            if self.connect():
                return self._execute(sql, args, fetch)
        
        return False
