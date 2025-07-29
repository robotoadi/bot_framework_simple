# n - e.g. 10
# sequence 1, 2, 3, 4, 5
# print as triangle


# for i print i numbers
nums = [i for i in range(0, 99)]
print(nums)

i = 1
result = []
max_lenght = 0
while len(nums) > 0:
    # take i numbers from the list
    curr = nums[:i]
    print(f'curr={curr}')
    result.append(curr)
    if len(curr) > max_lenght:
        max_lenght = len(curr)

    # print the appropriate amount of space before and after
        # need to know how long the longest line 
    
    i += 1
    nums = nums[i-1:]
    print(f'remaining: {nums}')


print(f'max_length: {max_lenght}')
i = 0
for curr_nums in result:
    buffer = max_lenght-i
    line = str(curr_nums).replace(',', '').replace('[', '').replace(']', '')
    print(f"{' '*buffer + line + ' '*buffer}")
    i += 1