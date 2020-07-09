from copy import deepcopy

from db_connection import DBConnection

from utils import *


class BaseTest(DBConnection):
    table_primary_key = "id"

    tables = {
        # "business": "business_id",
        "product_staging": "db_id",
        # "yelp_staging": table_primary_key,
        # "restaurant_detail_staging": table_primary_key,
        # "price_and_quantity_staging": table_primary_key,
        # "restaurant_price_and_qty_staging": table_primary_key,
    }

    def __init__(self):
        super().__init__()

    def grab_and_push_records(self, table, pk):
        log_info(f"Reading records from {table}...")
        query = f"SELECT * FROM `{table}` WHERE update_flag!=2 LIMIT {limit}"
        columns, records, record_ids = [], [], []
        bad_record_ids = set()
        columns_dict = {}

        try:
            self.sql_dict_cursor.execute(query)
            rows = self.sql_dict_cursor.fetchall()
            print(f"{len(rows)} records fetched from {table}")
            if not rows:
                self.tables.pop(table, '')
                return
            if table in ['business', 'product_staging']:
                columns_dict = self.get_table_fields_map(table)
                columns = list(columns_dict.keys())
            else:
                columns = list(rows[0].keys())

            columns.remove(pk)
            # columns.remove('update_flag')

            for rw in rows:
                try:
                    r = deepcopy(rw)
                    record_ids.append(str(r.pop(pk)))
                    r['update_flag'] = 2
                    # r.pop('update_flag', '')
                    r = clean_dict(r)
                    # records.append(tuple(r.values()))
                    r = {k.lower(): v for k, v in r.items()}
                    r = self.validate_data_type(r, columns_dict)
                    tuple_values = tuple([r[key] for key in columns if key.lower() != str(r[key]).lower()])
                    if len(columns) != len(tuple_values):
                        print(f"Founded Bad Record = {r}")
                        bad_record_ids.add(record_ids[-1])
                        continue
                    records.append(tuple_values)
                    log_info(r)
                except Exception as e:
                    log_info(f"Skipped record = {r}\nException\n{e}")
        except Exception as e:
            self.update_mysql_connection()
            log_info(f"Exception in grab_records: {e}")

        if bad_record_ids:
            self.delete_bad_records(table, bad_record_ids, pk)
        self.insert_records(table, columns, records, record_ids, pk)

    def validate_data_type(self, data, columns_dict):
        try:
            for key in data:
                if 'unknown' in key:
                    data[key] = None
                if [e in key for e in skipped_fields]:
                    continue
                elif columns_dict and 'int' in columns_dict.get(key, ''):
                    data[key] = int(data[key] or 0) if data[key] else 0
                elif columns_dict and 'text' in columns_dict.get(key, '') or 'varchar' in columns_dict.get(key, ''):
                    data[key] = clean(data[key])
        except Exception as e:
            print(e)
            a = 0

        a = 0
        return data

    def insert_records(self, table, columns, values, record_ids, pk="db_id"):
        if not values:
            return
        log_info(f"Inserting records into {table}")
        place_holders = ', '.join(['%s'] * len(columns))
        self.update_mysql_connection()

        try:
            query = f"INSERT INTO {table} ({', '.join(f'`{c}`' for c in columns)}) VALUES ({place_holders})"
            self.live_sql_conn_cursor.executemany(query, values)
            count = self.live_sql_conn_cursor.rowcount
            log_info(f"{count} records inserted in {table}", pre='')

            if not count:
                return
            self.update_record_ids(table, record_ids, pk)
            self.live_sql_connection.commit()
            self.sql_connection.commit()

        except Exception as e:
            log_info(f"Exception while inserting record in {table}\n{e}")

    def update_record_ids(self, table, record_ids, pk):
        try:
            log_info(f"Updating records IDs at localhost in {table}...")
            query = f"UPDATE {table} SET update_flag=2 WHERE {pk} IN ({', '.join(record_ids)})"
            self.sql_conn_cursor.execute(query)
            print(f"{self.sql_conn_cursor.rowcount} records updated at localhost in {table} SET update_flat = 2")
        except Exception as e:
            log_info(f"Exception while updating record IDs in {table}\n{e}")

    def delete_bad_records(self, table, bad_record_ids, pk):
        query = f"DELETE FROM {table} WHERE {pk} IN ({', '.join(bad_record_ids)})"
        self.sql_conn_cursor.execute(query)
        self.sql_connection.commit()
        log_info(f"{self.sql_conn_cursor.rowcount} bad records deleted from {table}")

    def get_table_columns(self, table_name, sql_cursor):
        try:
            if not sql_cursor:
                sql_cursor = self.sql_conn_cursor
            sql_cursor.execute(f"SHOW COLUMNS FROM {table_name}")
            # cols = [row[0] for row in sql_cursor.fetchall()]
            # cols_with_type = {r[0]: r[1] for r in sql_cursor.fetchall()}
            return [row for row in sql_cursor.fetchall()]
        except Exception as e:
            log_info(f"Exception while getting columns from {table_name}\n{e}")

    def get_table_fields_map(self, table):
        try:
            t1_cols = self.get_table_columns(table, self.sql_conn_cursor)
            t2_cols = self.get_table_columns(table, self.live_sql_conn_cursor)

            # return [c for c in t1_cols if c in t2_cols and 'unknown' not in c.lower()]
            t2c = [r2[0].lower() for r2 in t2_cols]
            return {r1[0].lower(): r2[1].lower() for r1, r2 in zip(t1_cols, t2_cols) if r1[0].lower() in t2c}
        except Exception as e:
            log_info(f"Exception in get_cols_from_mapper: {e}")
