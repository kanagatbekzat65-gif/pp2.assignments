def is_prime(n):
    if n < 2:
        return False
    for i in range(2, int(n ** 0.5) + 1):
        if n % i == 0:
            return False
    return True


numbers = list(map(int, input().split()))

primes = list(filter(lambda x: is_prime(x), numbers))

if primes:
    print(' '.join(map(str, primes)))
else:
    print("No primes")