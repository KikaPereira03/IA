class CakeSlice:
    color: str  # Color identifier (e.g. 'R', 'G', 'B')
    size: int

    def __init__(self, color, size=1):
        self.color = color
        self.size = size

    def __str__(self):
        return f"{self.color}{self.size}"