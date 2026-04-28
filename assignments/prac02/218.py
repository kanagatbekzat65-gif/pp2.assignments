n = int(input())
strings = []
for _ in range(n):
    strings.append(input())
first_occurrence = {}
for i, s in enumerate(strings, start=1):
    if s not in first_occurrence:
        first_occurrence[s] = i
unique_strings = sorted(first_occurrence.keys())
for s in unique_strings:
    print(s, first_occurrence[s])