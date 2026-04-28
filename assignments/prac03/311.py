class Pair:
    def __init__(self, a, b):
        self.a = a
        self.b = b
    
    def add(self, other):
        new_a = self.a + other.a
        new_b = self.b + other.b
        return Pair(new_a, new_b)


a1, b1, a2, b2 = map(int, input().split())

pair1 = Pair(a1, b1)
pair2 = Pair(a2, b2)

result_pair = pair1.add(pair2)

print(f"Result: {result_pair.a} {result_pair.b}")