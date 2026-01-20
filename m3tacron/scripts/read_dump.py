def read_chunks():
    with open('ui_dump.txt', 'r', encoding='utf-8', errors='ignore') as f:
        while True:
            chunk = f.read(1000)
            if not chunk: break
            print(chunk)
            
if __name__ == "__main__":
    read_chunks()
