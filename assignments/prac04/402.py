def gen(n):
    for i in range(0, n + 1):
        if i % 2 == 0:
            yield i

n = int(input())

first = True

for num in gen(n):
    if first:
        print(num, end="")
        first = False
    else:
        print("," + str(num), end="")