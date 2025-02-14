def func1(x):
    x = x + 2
    y = x
    z = x * (x - 2 + 3)  * y
    if z > x:
        z = 9
    elif z < y:
        x = 7
    else:
        z = 8
    return z + x + 1  

