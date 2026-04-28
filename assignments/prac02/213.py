a = int(input())

if a < 2:
    print("No")
else:
    is_prime = True
    for i in range(2, int(a**0.5) + 1):
        if a % i == 0:
            is_prime = False
            break
    print("Yes" if is_prime else "No")
