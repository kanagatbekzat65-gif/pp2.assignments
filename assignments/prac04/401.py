def sq(n):
    for i in range(1, n + 1):
        yield i * i

n = int(input())

for x in sq(n):
    print(x)