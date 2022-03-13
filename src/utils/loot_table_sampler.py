from typing import List, Tuple
from random import randint, sample
import numpy as np


class LootTablePool:
    """
    Container inventory generator, based on MC built-in loot table pools
    """
    def __init__(self, min_count, max_count):
        self.__min_count = min_count
        self.__max_count = max_count
        self.__entries = []
        self.__weights = []

    @classmethod
    def fromMCLootTable(cls, json_path: str):
        from json import load
        json_data = load(open(json_path))
        pool = json_data['pools'][0]
        rolls = pool['rolls']
        lt: LootTablePool = LootTablePool(int(rolls['min']), int(rolls['max']))
        for entry in pool['entries']:
            item = entry['name']
            weight = entry.get('weight', 1)
            if 'functions' in entry and any(_['function'] == 'minecraft:set_count' for _ in entry['functions']):
                count = next(filter(lambda _: _['function'] == 'minecraft:set_count', entry['functions']))['count']
                min_count = int(count['min'])
                max_count = int(count['max'])
            else:
                min_count = max_count = 1
            lt.addEntry(item, min_count, max_count, weight)
        return lt

    def addEntry(self, item: str, min_count: int = 1, max_count: int = 1, weight: int = 1) -> None:
        self.__entries.append((item, min_count, max_count))
        self.__weights.append(weight)

    def sampleInventory(self, containerWidth, containerHeight) -> List[Tuple[int, int, str, int]]:
        probs = np.array(self.__weights) / sum(self.__weights)
        items = []
        rolls = randint(self.__min_count, self.__max_count)
        for _ in range(rolls):
            entry = self.__entries[np.random.choice(range(len(self.__entries)), p=probs)]
            name = entry[0]
            count = randint(entry[1], entry[2])
            items.append((name, count))

        containerSize = containerWidth * containerHeight
        itemSlots = list(sample(range(containerSize), rolls))
        return [(slot % containerWidth, slot // containerWidth, item, amount) for ((item, amount), slot) in zip(items, itemSlots)]


if __name__ == '__main__':
    exampleLT: LootTablePool = LootTablePool.fromMCLootTable("resources/data_1.16.5/loot_tables/chests/village/village_plains_house.json")
    print(exampleLT.sampleInventory(9, 3))
