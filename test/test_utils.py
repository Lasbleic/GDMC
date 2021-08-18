from abc import ABC


class GDMCTest(ABC):
    def run(self):
        raise NotImplementedError("Abstract method")

    def erase(self, confirm_erase):
        return
