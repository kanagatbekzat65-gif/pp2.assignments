def valid(num):
    num_str=str(num)
    for digit_char in num_str:
        digit=int(digit_char)
        if digit%2!=0:
            return "Not valid"
    return "Valid"
num=int(input())
print(valid(num))