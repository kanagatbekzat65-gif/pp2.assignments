a=int(input())
count=0
b=list(map(int,input().split()))
for i in range(a):
    if b[i]>0:
        count+=1
    else:
        count+=0
print(count)