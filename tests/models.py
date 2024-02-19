class Foo:
    priority: int = 100

    def __lt__(self, other):
        return self.priority < other.priority


class Bar(Foo):
    pass


class Zap(Foo):
    priority: int = 90


class Bang(Foo):
    priority: int = 110
