def usual_num(n):
    for i in [2,3,5]:
        while n%i==0:
            n//=i
    return n==1
n=int(input())
if usual_num(n):
    print("Yes")
else:
    print("No")