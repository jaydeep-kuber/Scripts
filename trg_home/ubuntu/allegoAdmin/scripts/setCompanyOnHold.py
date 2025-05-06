import sys

def out():
    print("Received arguments:")
    for i, arg in enumerate(sys.argv):
        print(f"Arg {i}: {arg}")

print(">>> Company holding script")
out()
