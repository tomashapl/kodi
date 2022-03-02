import os
from functools import partial
import json
import time
import ssl
import xbmc
import websocket


def get_is_playing(ws):
    is_playing = xbmc.Player().isPlaying()
    print("is playing {0}".format(is_playing))
    ws.send(json.dumps({"isPlaying": bool(is_playing)}))


def execute_build_in(ws, params):
    print("execute_build_in", params)
    xbmc.executebuiltin(params, True)
    ws.send(
        json.dumps(
            {"executed": bool(True), "command": "execute_build_in", "params": params}
        )
    )


def get_playing_stream(ws):
    print("get stream")
    is_playing = xbmc.Player().isPlaying()

    if is_playing:
        player = xbmc.Player()
        current_stream = player.getPlayingFile()
        playing_time = player.getTime()
        ws.send(
            json.dumps(
                {
                    "isPlaying": bool(True),
                    "stream": current_stream,
                    "time": playing_time,
                }
            )
        )
    else:
        ws.send(json.dumps({"isPlaying": bool(False)}))


def on_message(ws, message):
    command_message = json.loads(message)
    switcher = {
        "execute_build_in": partial(execute_build_in, ws, command_message["params"]),
        "get_playing_stream": partial(get_playing_stream, ws),
        "get_is_playing": partial(get_is_playing, ws)
    }

    call = switcher.get(command_message["command"], lambda: "Invalid command")
    call()


def on_error(ws, error):
    print(error)


def on_close(ws, close_status_code, close_msg):
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

            address = "wss://lili.psvz.cz/websockets"
            #address = "ws://localhost:8080"

            ws = websocket.WebSocketApp(
                address,
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
