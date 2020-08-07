import time

from db_connection import DBConnection

from utils import *


class Base(DBConnection):
    tables = {}

    product_staging_map = {
        "store_id": "business_id",
        "item_name": "name",
        "img_src": "images",
        "db_id": "id",
    }

    def grab_and_push_records(self, table, fields_map, pk, retry_times=0):
        log_info(f"Reading records from {table}...")
        query = f"SELECT * FROM `{table}` WHERE update_flag NOT IN (2, 6) LIMIT {limit}"

        records, record_ids = [], []
        bad_record_ids = set()

        try:
            self.sql_dict_cursor.execute(query)
            rows = self.sql_dict_cursor.fetchall()
            print(f"{len(rows)} rows fetched from {table}")

            # Bad Records Ids if store not exists in business table
            bad_ids, rows = self.get_bad_records_ids(table, rows, pk)
            if bad_ids:
                print(f"{len(bad_ids)} Bad Records found with stores id have not registered in business")
                self.delete_bad_records(table, bad_ids, pk)

            if not rows and not bad_ids:
                self.tables.pop(table, '')
                return
            fields_map.pop(pk)

            for r in rows:
                try:
                    record_ids.append(str(r.pop(pk)))
                    r = clean_dict(r)
                    r = {k.lower(): v for k, v in r.items()}
                    r['update_flag'] = 2
                    tuple_val = tuple([r[key] for key in fields_map.keys() if key.lower() != str(r[key]).lower()])

                    if len(fields_map) != len(tuple_val):
                        print(f"Founded Bad Record = {r}")
                        bad_record_ids.add(record_ids[-1])
                        continue

                    records.append(tuple_val)
                    # log_info(r)
                except Exception as e:
                    log_info(f"Skipped bad record = {r}\nException\n{e}")
        except Exception as e:
            if self.can_retry(f"Exception in grab_records: {e}", retry_times):
                self.grab_and_push_records(table, fields_map, pk, retry_times + 1)
                return

        if bad_record_ids:
            self.update_records_flag(table, bad_record_ids, pk, flag=6)
            self.sql_connection.commit()

        self.insert_records(table, fields_map.values(), records, record_ids, pk)

    def insert_records(self, table, columns, values, record_ids, pk="db_id", retry_times=0):
        if not values:
            return
        log_info(f"Inserting records into {self.tables[table]['live_tab']}...")
        place_holders = ', '.join(['%s'] * len(columns))
        query = f"INSERT INTO {self.tables[table]['live_tab']} " \
                f"({', '.join(f'`{c}`' for c in columns)}) VALUES ({place_holders})"

        try:
            self.update_mysql_connection()
            self.live_sql_conn_cursor.executemany(query, values)
            count = self.live_sql_conn_cursor.rowcount
            log_info(f"{count} records inserted in {self.tables[table]['live_tab']}", pre='')
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
        if not bad_record_ids:
            return

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

    def get_bad_records_ids(self, table, rows, pk, retry_times=0):
        # get bad records ids if store_id has not been registered in business table
        bad_ids = set()
        valid_rows = []

        try:
            if table not in ["business", "yelp_staging"] and rows:
                biz_ids = {r['store_id'] for r in rows}
                query = f"SELECT business_id from `business` WHERE business_id " \
                        f"IN ({', '.join(str(e) for e in biz_ids)})"
                self.sql_conn_cursor.execute(query)
                match_ids = {r[0] for r in self.sql_conn_cursor.fetchall()}

                for r in rows:
                    if r['store_id'] not in match_ids:
                        bad_ids.add(str(r[pk]))
                        continue
                    valid_rows.append(r)

        except Exception as e:
            if self.can_retry(f"Exception while deleting delete_bad_records: {e}", retry_times):
                self.get_bad_records_ids(table, rows, pk, retry_times + 1)

        return bad_ids, valid_rows

    def get_table_columns(self, table_name, sql_cursor):
        try:
            sql_cursor.execute(f"SHOW COLUMNS FROM {table_name}")
            return [row[0].lower() for row in sql_cursor.fetchall()]
        except Exception as e:
            log_info(f"Exception while getting columns from {table_name}\n{e}")

    def get_table_fields_map(self, table, retry_times=0):
        try:
            t1_cols = self.get_table_columns(table, self.sql_conn_cursor)
            t2_cols = self.get_table_columns(self.tables[table]['live_tab'], self.live_sql_conn_cursor)
            if table != "product_staging":
                return {c: c for c in t1_cols if c in t2_cols}
            else:
                return {c1: c1 if c1 in t2_cols else self.product_staging_map[c1] for c1 in t1_cols
                        if c1 in t2_cols or c1 in self.product_staging_map}

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
