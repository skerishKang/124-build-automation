import time, random, functools

def retry(backoffs=(1,2,4), retry_on=(429,500,502,503,504)):
    def deco(fn):
        @functools.wraps(fn)
        def wrapper(*a, **kw):
            tries = len(backoffs)+1
            for i in range(tries):
                try:
                    return fn(*a, **kw)
                except Exception as e:
                    msg = str(e)
                    code = next((c for c in retry_on if str(c) in msg), None)
                    if i == tries-1 or code is None:
                        raise
                    time.sleep(backoffs[i] + random.random())
        return wrapper
    return deco
