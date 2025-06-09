def func1(x,a,b):
    y = 0
    for i in range(1000):
        x.append(10)
        x.extend(x)
        x+=5
        x[0]*=2
        y = 4 + i
    names=[]
    for i in x:
        y += i + 5
        names.append(y)
    for key, value in d.items():
        x += value
    for index, name in enumerate(names):
       x.append(f"{name}{index}")
       x.append(y)
    a = x
    b = x
    for i, j in zip(a, b):
        x.extend([a,b])
       
    
    