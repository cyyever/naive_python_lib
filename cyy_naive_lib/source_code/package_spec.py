import re

from looseversion import LooseVersion


class PackageSpecification:
    default_branch = "main"

    @staticmethod
    def compare_version(ver1: str, ver2: str) -> int:
        if ver1 in ("master", "main"):
            if ver2 in ("master", "main"):
                return 0
            return 1

        if ver2 in ("master", "main"):
            return -1

        if ver1.startswith("v"):
            ver1 = ver1[1:]
        if ver2.startswith("v"):
            ver2 = ver2[1:]

        if LooseVersion(ver1) < LooseVersion(ver2):
            return -1
        if LooseVersion(ver1) > LooseVersion(ver2):
            return 1
        return 0

    def __init__(self, specification: str) -> None:
        match_res = re.match(
            "^([a-zA-Z0-9_-]+)(\\[(.*)\\])?(:[a-zA-Z0-9_./-]+)?$", specification
        )
        if match_res is None:
            raise ValueError("unsupported package specification:" + specification)

        self.name: str = match_res.group(1)
        self.features = match_res.group(3)
        self.branch: str = ""
        matched_branch: str = match_res.group(4)
        if matched_branch:
            self.branch = matched_branch[1:]
        else:
            self.branch = self.default_branch
        if self.features is not None:
            self.features = set(self.features.split(","))
        else:
            self.features = set()

    def __repr__(self) -> str:
        res = self.name
        if self.features:
            res += "[" + ",".join(sorted(self.features)) + "]"
        if self.branch == self.default_branch:
            return res
        return res + ":" + self.branch

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, PackageSpecification):
            return NotImplemented
        return self.name == other.name and self.branch == other.branch

    def __ne__(self, other: object) -> bool:
        if not isinstance(other, PackageSpecification):
            return NotImplemented
        return not self.__eq__(other)

    def __hash__(self) -> int:
        return hash((self.name, self.branch))
