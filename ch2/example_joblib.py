# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "joblib",
# ]
# ///
import time

from joblib import Memory

cachedir = "./cachedir"
memory = Memory(cachedir, verbose=0)


@memory.cache
def my_function(x, y):
    time.sleep(5)
    return x + y


print(my_function(1, 2))
print(my_function(1, 2))
