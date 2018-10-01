import psycopg2


class DAO(object):
    """
    Handles database access and provides methods for performing operations
    """
    def __init__(self):
        self.conn = psycopg2.connect("host='postgres' user='postgres' password='postgres' dbname='postgres'")
        self.cursor = self.conn.cursor()


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


    def commit(self):
        return self.conn.commit()


    def rollback(self):
        return self.conn.rollback()


    def close(self):
        return self.conn.close()