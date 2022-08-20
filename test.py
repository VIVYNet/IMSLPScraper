import concurrent.futures
import time

def foo(data):
    print(data)
    time.sleep(2)
    
a = ["A", "B", "C", "D", "E"]
b = [str(i) for i in range(45)]

if __name__ == '__main__':
    for i in a:
        print("TESTING " + i) 
        with concurrent.futures.ProcessPoolExecutor() as executor:
            _ = [executor.submit(foo, (i + j)) for j in b]