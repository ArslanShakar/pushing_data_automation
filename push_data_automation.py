import time
from copy import deepcopy
import csv

from base import Base


class PushDataAutomation(Base):
    def __init__(self, tables_dict):
        super().__init__()
        self.tables = deepcopy(tables_dict)
        self.push_data_to_live_database()

        self.get_table_schema('business')
        self.get_table_schema('product_staging')
        self.get_table_schema('price_and_quantity_staging')

    def get_table_schema(self, table_name):
        try:
            csv_writer = self.get_csv_writer_write_headers(table_name+'.csv')

            self.live_sql_conn_cursor.execute(f"SHOW COLUMNS FROM {table_name}")
            for row in self.live_sql_conn_cursor.fetchall():
                item = {'Name': row[0], 'Type': row[1],
                        'Nullable': row[2], 'Default Value': row[4],
                        'Extra_Info': row[-1].lower()}
                self.write_item_to_csv(csv_writer, item)

        except Exception as e:
            print(f"Exception while getting columns\n{e}")

    def get_csv_writer_write_headers(self, file_name):
        file = open(file_name, "a+")
        csv_writer = csv.writer(file, delimiter=',')
        csv_writer.writerow(['Name', 'Type', 'Default Value', 'Nullable', 'Extra_Info'])
        return csv_writer

    def write_item_to_csv(self, csv_writer, item):
        csv_writer.writerow([item['Name'], item['Type'], item['Default Value'],
                             item['Nullable'], item['Extra_Info']])

    def push_data_to_live_database(self):
        fields_map = {tab: self.get_table_fields_map(tab) for tab in self.tables}

        while self.tables:
            try:
                for tab, item in self.tables.items():
                    self.grab_and_push_records(tab, deepcopy(fields_map[tab]), item['pk'])
                    time.sleep(2)
            except Exception as e:
                pass


if __name__ == "__main__":
    table_primary_key = "id"

    tables = {
        "business": {'pk': "business_id", "live_tab": "business_import"},
        "product_staging": {'pk': "db_id", "live_tab": "products"},
        "yelp_staging": {'pk': table_primary_key, "live_tab": "yelp_staging"},
        "restaurant_detail_staging": {'pk': table_primary_key, "live_tab": "restaurant_detail_live"},
        "price_and_quantity_staging": {'pk': table_primary_key, "live_tab": "price_and_quantity_live"},
        "restaurant_price_and_qty_staging": {'pk': table_primary_key, "live_tab": "restaurant_price_and_qty_live"},
    }

    while True:
        PushDataAutomation(tables)
        print('Sleeping for 30 minutes...')
        time.sleep(60 * 30)
