a=int(input())
b=list(map(int,input().split()))
c=set()
for i in range(a):
    if b[i] not in c:
        print("YES")
        c.add(b[i])
    else:
        print("NO")