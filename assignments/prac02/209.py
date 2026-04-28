a=int(input())
b=list(map(int,input().split()))
x=max(b)
y=min(b)
for i in range(a):
    if b[i]==x:
        b[i]=y
print(*b)