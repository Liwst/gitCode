import time
def timer(func):
    def wrapper(*args,  **kwargs):
        start = time.time()
        res = func(*args,  **kwargs)
        print(f"{func.__name__}耗时：{time.time()-start:.2f}s")
        return res
    return wrapper

@timer
def train_model():
    time.sleep(2)
train_model()