import time
from copy import deepcopy

from base import Base
from base_test import BaseTest


class PushDataAutomation(Base):
    def __init__(self):
        super().__init__()
        self.push_data_to_live_database()

    def push_data_to_live_database(self):
        fields_map = {tab: self.get_table_fields_map(tab) for tab in self.tables}

        while self.tables:
            try:
                for tab, pk in self.tables.items():
                    self.grab_and_push_records(tab, deepcopy(fields_map[tab]), pk)
                    time.sleep(2)
            except Exception as e:
                pass


if __name__ == "__main__":
    PushDataAutomation()
