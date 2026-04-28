def string_calculator(s):
    to_digit = {
        "ZER": 0, "ONE": 1, "TWO": 2, "THR": 3,
        "FOU": 4, "FIV": 5, "SIX": 6, "SEV": 7,
        "EIG": 8, "NIN": 9
    }
    to_triplet = {v: k for k, v in to_digit.items()}

    if '+' in s:
        left, right = s.split('+')
        op = '+'
    elif '-' in s:
        left, right = s.split('-')
        op = '-'
    elif '*' in s:
        left, right = s.split('*')
        op = '*'
    else:
        raise ValueError("No operator found")


    def triplet_to_int(triplet_str):
        num = 0
        for i in range(0, len(triplet_str), 3):
            chunk = triplet_str[i:i+3]
            num = num * 10 + to_digit[chunk]
        return num

    left_num = triplet_to_int(left)
    right_num = triplet_to_int(right)


    if op == '+':
        result_num = left_num + right_num
    elif op == '-':
        result_num = left_num - right_num
    else:  # '*'
        result_num = left_num * right_num


    if result_num == 0:
        return "ZER"

    result_str = ""
    for ch in str(result_num):
        result_str += to_triplet[int(ch)]

    return result_str

s = input().strip()
print(string_calculator(s))