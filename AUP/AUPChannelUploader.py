import sys

def main():
    print("Received arguments:")
    for i, arg in enumerate(sys.argv):
        print(f"Arg {i}: {arg}")

if __name__ == "__main__":
    print(">>> AUP uploading script")
    main()
