a=int(input())
c=list(map(int,input().split()))
b=0
for i in range(a):
    b+=c[i]
print(b)