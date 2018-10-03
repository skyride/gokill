from celery.signals import worker_process_init, worker_process_shutdown
import psycopg2
import redis

db_conn = None
redis_conn = None

class DAO(object):
    """
    Handles database access and provides methods for performing operations
    """
    def __init__(self):
        self.db_conn = psycopg2.connect("host='postgres' user='postgres' password='postgres' dbname='postgres'")
        self.cursor = self.db_conn.cursor()
        self.redis = redis_conn


    def execute(self, *args, **kwargs):
        return self.cursor.execute(*args, **kwargs)


    def execute_many(self, sql, values):
        """
        Takes an SQL query and appends VALUES sets on the end
        """
        if len(values) > 0:
            template = "(%s)" % ", ".join("%s" for _ in range(len(values[0])))
            sql_values = ", ".join([template for value in values])
            values = sum(values, ())
            return self.cursor.execute(
                sql + sql_values,
                values
            )

    def fetchall(self):
        return self.cursor.fetchall()


    def commit(self):
        return self.db_conn.commit()


    def rollback(self):
        return self.db_conn.rollback()


    def close(self):
        return self.db_conn.close()


@worker_process_init.connect
def create_connections(**kwargs):
    """Creates database connections when workers launch"""
    global db_conn, redis_conn
    #db_conn = psycopg2.connect("host='postgres' user='postgres' password='postgres' dbname='postgres'")
    redis_conn = redis.Redis(host="redis")


@worker_process_shutdown.connect
def close_connections(**kwargs):
    """Closes database connections when workers close"""
    global db_conn, redis_conn
    #db_conn.close()