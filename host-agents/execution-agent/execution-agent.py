import subprocess
import sys


def main():
    for i in range(0, int(sys.argv[1])):
        with open("/tmp/output.log", "a") as output:
            subprocess.Popen(
                "python3 vmModule.py", shell=True, stdout=output, stderr=output
            )


if __name__ == "__main__":
    main()
