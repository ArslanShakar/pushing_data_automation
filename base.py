import time

from db_connection import DBConnection

from utils import *


class Base(DBConnection):
    table_primary_key = "id"

    tables = {
        "business": "business_id",
        "product_staging": "db_id",
        "yelp_staging": table_primary_key,
        "restaurant_detail_staging": table_primary_key,
        "price_and_quantity_staging": table_primary_key,
        "restaurant_price_and_qty_staging": table_primary_key,
    }

    def grab_and_push_records(self, table, columns, pk, retry_times=0):
        log_info(f"Reading records from {table}...")
        query = f"SELECT * FROM `{table}` WHERE update_flag NOT IN (2, 6) LIMIT {limit}"

        records, record_ids = [], []
        bad_record_ids = set()

        try:
            self.sql_dict_cursor.execute(query)
            rows = self.sql_dict_cursor.fetchall()
            print(f"{len(rows)} rows read from {table}")

            if not rows:
                self.tables.pop(table, '')
                return
            columns.remove(pk)

            for r in rows:
                try:
                    record_ids.append(str(r.pop(pk)))
                    r = clean_dict(r)
                    r = {k.lower(): v for k, v in r.items()}
                    r['update_flag'] = 2

                    tuple_val = tuple([r[key] for key in columns if key.lower() != str(r[key]).lower()])
                    if len(columns) != len(tuple_val):
                        print(f"Founded Bad Record = {r}")
                        bad_record_ids.add(record_ids[-1])
                        continue

                    records.append(tuple_val)
                    log_info(r)
                except Exception as e:
                    log_info(f"Skipped bad record = {r}\nException\n{e}")
        except Exception as e:
            if self.can_retry(f"Exception in grab_records: {e}", retry_times):
                self.grab_and_push_records(table, columns, pk, retry_times + 1)
                return

        if bad_record_ids:
            self.update_records_flag(table, bad_record_ids, pk, flag=6)
            self.sql_connection.commit()

        self.insert_records(table, columns, records, record_ids, pk)

    def insert_records(self, table, columns, values, record_ids, pk="db_id", retry_times=0):
        if not values:
            return
        log_info(f"Inserting records into {table}...")
        place_holders = ', '.join(['%s'] * len(columns))
        query = f"INSERT INTO {table} ({', '.join(f'`{c}`' for c in columns)}) VALUES ({place_holders})"

        try:
            self.update_mysql_connection()
            self.live_sql_conn_cursor.executemany(query, values)
            count = self.live_sql_conn_cursor.rowcount
            log_info(f"{count} records inserted in {table}", pre='')
            if not count:
                return

            self.update_records_flag(table, record_ids, pk)
            self.live_sql_connection.commit()
            self.sql_connection.commit()
        except Exception as e:
            if self.can_retry(f"Exception while inserting record in {table}\n{e}", retry_times):
                self.insert_records(table, columns, values, record_ids, pk, retry_times + 1)
                return

    def update_records_flag(self, table, record_ids, pk, flag=2, retry_times=0):
        if not record_ids:
            return
        try:
            log_info(f"Updating record ids in {table} by update_flag = {flag}...")
            query = f"UPDATE {table} SET update_flag={flag} WHERE {pk} IN ({', '.join(record_ids)})"
            self.sql_conn_cursor.execute(query)
            print(f"{self.sql_conn_cursor.rowcount} rows updated in {table}")
        except Exception as e:
            if self.can_retry(f"Exception while updating record IDs in {table}\n{e}", retry_times + 1):
                self.update_records_flag(table, record_ids, pk, flag, retry_times + 1)
                return

    def delete_bad_records(self, table, bad_record_ids, pk, retry_times=0):
        try:
            log_info(f"Deleting bad records {table}...")
            query = f"DELETE FROM {table} WHERE {pk} IN ({', '.join(bad_record_ids)})"
            self.sql_conn_cursor.execute(query)
            self.sql_connection.commit()
            log_info(f"{self.sql_conn_cursor.rowcount} bad records deleted from {table}")
        except Exception as e:
            if self.can_retry(f"Exception while deleting delete_bad_records: {e}", retry_times):
                self.delete_bad_records(table, bad_record_ids, pk, retry_times + 1)
                return

    def get_table_columns(self, table_name, sql_cursor):
        try:
            sql_cursor.execute(f"SHOW COLUMNS FROM {table_name}")
            return [row[0].lower() for row in sql_cursor.fetchall()]
        except Exception as e:
            log_info(f"Exception while getting columns from {table_name}\n{e}")

    def get_table_fields_map(self, table, retry_times=0):
        try:
            t1_cols = self.get_table_columns(table, self.sql_conn_cursor)
            t2_cols = self.get_table_columns(table, self.live_sql_conn_cursor)
            return [c for c in t1_cols if c in t2_cols]
        except Exception as e:
            if self.can_retry(f"Exception in get_table_fields_map: {e}", retry_times):
                self.get_table_fields_map(table, retry_times + 1)
                return

    def can_retry(self, log, retry_times):
        if retry_times == 2:
            return

        time.sleep(wait_time_seconds)
        self.update_mysql_connection()
        log_info(log)
        return True
