with open('backend_err.txt', 'r') as f:
    lines = f.readlines()
idx = len(lines) - 1
while idx >= 0:
    if 'ValidationError' in lines[idx]:
        print("".join(lines[idx:idx+30]))
        break
    idx -= 1
