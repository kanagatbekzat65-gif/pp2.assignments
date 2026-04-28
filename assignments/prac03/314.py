n = int(input())
arr = list(map(int, input().split()))
q = int(input())

for _ in range(q):
    operation = input().split()
    
    if operation[0] == "add":
        x = int(operation[1])
        arr = list(map(lambda a: a + x, arr))
    
    elif operation[0] == "multiply":
        x = int(operation[1])
        arr = list(map(lambda a: a * x, arr))
    
    elif operation[0] == "power":
        x = int(operation[1])
        arr = list(map(lambda a: a ** x, arr))
    
    elif operation[0] == "abs":
        arr = list(map(lambda a: abs(a), arr))

print(' '.join(map(str, arr)))