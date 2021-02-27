from subprocess import Popen, PIPE, STDOUT, call
import re
import xbmc

actions = {
    "unplugged": "stop",
    "attached": "start",
}


def get_line_action(state):
    command = actions.get(state, "Invalid command")
    call(["systemctl", command, "service.hyperion"])


if __name__ == "__main__":
    monitor = xbmc.Monitor()

    process = Popen(
        "tvservice -M 2>&1",
        shell=True,
        stderr=STDOUT,
        stdout=PIPE,
    )

    while True:
        output = process.stdout.readline()
        if output == "" and process.poll() is not None:
            break
        if output:
            decoded = output.decode("utf-8")
            if re.search("attached", decoded):
                get_line_action("attached")
            if re.search("unplugged", decoded):
                get_line_action("unplugged")

    while monitor.abortRequested:
        process.kill()
