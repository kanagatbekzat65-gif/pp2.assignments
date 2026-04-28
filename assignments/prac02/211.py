a,b,c= map(int, input().split())
x=list(map(int,input().split()))
b-=1
c-=1
while b<c:
    x[b],x[c]=x[c],x[b]
    b+=1
    c-=1        
print(*x)
