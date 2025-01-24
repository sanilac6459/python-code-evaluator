# Pythonic Code Evaluator
This is a Pythonic code evaluator that's takes in user's Python code to determine whether it's Pythonic or not, along with providing a more Pythonic version of their code and analyzing the outputs between the two.

## How it works:
* The user is prompted to enter a Python code. The code _must_ be Python. If they enter a different programming language, they will be reprompted to enter only Python code.
* Once user enters a Python code, it will determine whether the code is Pythonic or not and providing a brief explanation of why it is or isn't.
* If the code is NOT Pythonic, suggestions will be provided and the user can choose to see the more Pythonic and the outputs between their code and the Pythonic version.
    * If they choose to see it, the more Pythonic version of their code will be provided and the comparsion between the two code in which the user can see the similarities and differences.

### Example where user's code is NOT Pythonic:
Please enter a Python code:
_(sorting a list in ascending order)_
```python
my_list = [1, 12, 41, 5, 60, 37, 29]

for i in range(len(my_list)):
    for j in range(0, len(my_list) - i - 1):
        if my_list[j] > my_list[j + 1]:
            my_list[j], my_list[j + 1] = my_list[j + 1], my_list[j]

print(my_list)
```

Thank you for providing Python code. Please wait...

Is the code Pythonic or not: No

Explanation:
- The code manually implements the bubble sort algorithm to sort a list, which is less efficient and not pythonic.
- Using built-in python functions and methods can make the code more concise, readable, and efficient.

Suggestions:
- Use python's built-in sorting functions like `sorted()` or `list.sort()`, which are more efficient and idiomatic.
- Avoid creating a new list `new_list` if it is not being used in the code.
- Follow python's pep 8 style guide for better code readability, such as placing each statement on a new line.

Would you like to see the more Pythonic version of your code and the output between the two? (y/n): y


Here's the more Pythonic version of your code:
```python
my_list = [1, 12, 41, 5, 60, 37, 29]
sorted_list = sorted(my_list)
print(sorted_list)
```

Using python's built-in `sorted()` function is more preferable because it is easier to read, requires fewer lines of code, and utilizes highly optimized and tested sorting algorithms which are likely more efficient than a custom implementation, such as the bubble sort seen in the original code.


Comparing the outputs:


Outputs:
```
user code output: [1, 5, 12, 29, 37, 41, 60]
pythonic code output: [1, 5, 12, 29, 37, 41, 60]
```

Similarities and Differences:
- Similarities: both the user-provided code and the pythonic code produce the same sorted list `[1, 5, 12, 29, 37, 41, 60]`. this indicates that both implementations correctly sort the given list in ascending order.
- Differences: there is no difference in the final output of the two versions of the code. the difference lies in the implementation; the user code manually implements the bubble sort algorithm, while the pythonic code utilizes python's built-in `sorted()` function for sorting.

### Example where user's code _is_ Pythonic:
Please enter a Python code:
_(reverse the order of the list)_
```python
my_list = [1, 2, 3, 4, 5]
reversed_list = my_list[::-1]
print(reversed_list)
```

Thank you for providing Python code. Please wait...


Is the code Pythonic or not: Yes

This code is pythonic as it uses slicing to reverse a list, which is a common and clear idiomatic approach in python. the code is concise and leverages python's syntactic sugar effectively.

Your code is already Pythonic!