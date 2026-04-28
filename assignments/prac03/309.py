class Circle:
    pi = 3.14159 
    def __init__(self, radius):
        self.radius = radius
    def area(self):
        return self.pi * self.radius * self.radius
r = int(input())
circle = Circle(r)
print(f"{circle.area():.2f}")