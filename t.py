def isValid(s: str) -> bool:
    res=[]
    if not s: return True
    for c in s:
        print(c)
        if c == '[' or  c == '{' or c == '(':
            res.append[c]
        elif c == ']' :
            if res[-1] == '[':
                res.pop()
        elif c == '}': 
            if res[-1] == '{':
                res.pop()
        elif c ==')': 
            if res[-1] == '(':
                res.pop()
        else:
            continue
    print(res)

    return True if res.len()==0 else False 
s="[(])"
isValid(s)
