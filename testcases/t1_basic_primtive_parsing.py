def func1(x):
    return x[0] + 1

def func2(x):
    pass
if __name__ == '__main__':
    x = [5,2,3,4,5]
    y = x[0] + 3
    z = x[-1] * y
    x = x[2:4] + [2,2]
    y = x 
    if z > x[2]:
        z=9
    elif z < y[0]:
        z=7
    else:
        z=8
    l = func1(x)
    func2(l)