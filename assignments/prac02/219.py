n = int(input())
dramas = {}
for _ in range(n):
    s, k = input().split()
    k = int(k)
    if s in dramas:
        dramas[s] += k
    else:
        dramas[s] = k
for name in sorted(dramas.keys()):
    print(name, dramas[name])