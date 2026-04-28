n = int(input())
numbers = list(map(int, input().split()))
freq = {}
for x in numbers:
    if x in freq:
        freq[x] += 1
    else:
        freq[x] = 1
most_common = None
max_count = -1
for x in numbers:
    count = freq[x]
    if count > max_count or (count == max_count and x < most_common):
        max_count = count
        most_common = x
print(most_common)