n = int(input())
contacts = []
for _ in range(n):
    contacts.append(input())
freq = {}
for num in contacts:
    freq[num] = freq.get(num, 0) + 1
count = 0
for num in freq:
    if freq[num] == 3:
        count += 1
print(count)