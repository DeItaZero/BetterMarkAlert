import json
import sys
import time

import requests
import urllib3
from custom_types import *

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
TIMEOUT = 5, 40


class MarkAlert:
    def __init__(self, modules: list[module_type]):
        self.modules = modules
        self.distributions: dict[module_type, dist_type] = {}
        self._load_distributions()
        self.callables: set[callable_type] = set()

    def _load_distributions(self):
        with open(r"distributions.json", "r", encoding="utf-8") as f:
            self.distributions = json.load(f)

    def _save_distributions(self):
        with open(r"distributions.json", "w", encoding="utf-8") as f:
            json.dump(self.distributions, f, ensure_ascii=False, indent=2)

    @staticmethod
    def get_dist(module: module_type) -> dist_type:
        code, year, period = module
        result = requests.get(f"https://selfservice.campus-dual.de/acwork/mscoredist?"
                              f"module={code}&peryr={year}&perid={period}", verify=False, timeout=TIMEOUT)
        return result.json()

    @staticmethod
    def get_count(dist: dist_type) -> int:
        count = 0
        for mark in dist:
            count += mark["COUNT"]
        return count

    @staticmethod
    def get_module_str(module: module_type) -> str:
        return "|".join(module)

    @staticmethod
    def get_new_marks(old_dist: dist_type, new_dist: dist_type) -> int:
        return MarkAlert.get_count(new_dist) - MarkAlert.get_count(old_dist)

    def get_old_dist(self, module: module_type) -> dist_type | None:
        return self.distributions.get(MarkAlert.get_module_str(module), None)

    def add_callable(self, callable: callable_type) -> None:
        self.callables.add(callable)

    def call(self, module: module_type, old_dist: dist_type, new_dist: dist_type) -> None:
        for callable in self.callables:
            callable(module, old_dist, new_dist)

    def check(self, module: module_type):
        old_dist = self.get_old_dist(module)
        sys.stdout.write(f"{MarkAlert.get_module_str(module)}: ")
        try:
            new_dist = MarkAlert.get_dist(module)
        except Exception:
            print("Noten konnten nicht geladen werden!")
            return

        if old_dist is not None:
            new_marks = MarkAlert.get_new_marks(old_dist, new_dist)
            if new_marks > 0:
                self.call(module, old_dist, new_dist)
                print("Neue Noten wurden geladen!")
            elif new_marks < 0:
                print("Noten wurden entfernt!")
            else:
                print("Noten haben sich nicht geändert")

        self.distributions[MarkAlert.get_module_str(module)] = new_dist
        self._save_distributions()

    def run(self):
        for module in self.modules:
            self.check(module)

