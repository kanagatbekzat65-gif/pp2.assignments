a=int(input())
b=list(map(int,input().split()))
newlist=[]
for i in range(a):
    (b[i])**=2
print(*b) 