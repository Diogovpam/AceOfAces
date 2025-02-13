from typing import List

import pandas as pd

from src.entities.entities import Page, Factions, Movement, DetailedMovement
from src.entities.move_defaults import DEFAULT_MOVE_LIST


class PageManager:

    def __init__(self, faction: Factions):
        self.faction = faction
        self.move_file_path = f"../data/aoa_{faction}.csv"
        self.move_df = pd.read_csv(self.move_file_path)

    @staticmethod
    def load_moves(page_row) -> List[Movement]:
        move_list = []

        for idx, default_move in enumerate(DEFAULT_MOVE_LIST):
            move = DetailedMovement(
                next_page=page_row[f'm_{idx}'],
                **default_move.dict(exclude_none=True)
            )

            move_list.append(move)

        return move_list

    def load_page(self, page_num: int = 170) -> Page:
        page_row = self.move_df.iloc[page_num-1]

        return Page(
            faction=self.faction,
            page_num=page_num,
            distance=page_row['distance'],
            tail=page_row['tail'],
            fire=page_row['fire'],
            moves=self.load_moves(page_row)
        )

    def find_result(self, mid_page_num, movement_index) -> int:
        mid_page_row = self.move_df.iloc[mid_page_num-1]
        return int(mid_page_row[f'm_{movement_index}'])

