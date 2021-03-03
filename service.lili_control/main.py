import os
from functools import partial
import json
import time
import ssl
import xbmc
import websocket


def execute_build_in(ws, params):
    print("execute_build_in", params)
    xbmc.executebuiltin(params)


def get_playing_stream(ws):
    print("get stream")
    current_stream = xbmc.Player().getPlayingFile()
    ws.send(json.dumps({"stream": current_stream}))


def on_message(ws, message):
    command_message = json.loads(message)
    switcher = {
        "execute_build_in": partial(execute_build_in, ws, command_message["params"]),
        "get_playing_stream": partial(get_playing_stream, ws),
    }

    call = switcher.get(command_message["command"], lambda: "Invalid command")
    call()


def on_error(ws, error):
    print(error)


def on_close(ws):
    print("### closed ###")


def on_open(ws):
    print("Opened")


def connect():
    while True:
        try:
            secrets = {
                "secret": "EE71C236BEC72A259BACAB36562FC",
                "id": os.uname()[1],
            }
            websocket.enableTrace(True)
            ws = websocket.WebSocketApp(
                "wss://lili.psvz.cz/websockets",
                on_open=on_open,
                on_message=on_message,
                on_error=on_error,
                on_close=on_close,
                header=["authorization: {0}".format(json.dumps(secrets))],
            )

            ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
        except Exception as e:
            print("Websocket connection Error  : {0}".format(e))
            time.sleep(5)


if __name__ == "__main__":
    connect()
