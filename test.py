with open('user.txt', 'r',encoding='utf-8') as fobj:
    user = fobj.readlines()
    user = tuple([i.strip('\n') for i in user])


print(user)