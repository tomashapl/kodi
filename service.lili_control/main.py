import os
import json
import xbmc
import ssl
import websocket


def on_message(ws, message):
    print(message)
    xbmc.executebuiltin(message)


def on_error(ws, error):
    print(error)


def on_close(ws):
    print("### closed ###")


def on_open(ws):
    def run(*args):
        for i in range(3):
            ws.send("Hello %d" % i)
        ws.close()
        print("thread terminating...")


if __name__ == "__main__":

    secrets = {
        "secret": "EE71C236BEC72A259BACAB36562FC",
        "id": xbmc.getInfoLabel("System.FriendlyName") or os.uname()[1],
    }

    websocket.enableTrace(True)
    ws = websocket.WebSocketApp(
        "wss://lili.psvz.cz/websockets",
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
        header=["authorization: {0}".format(json.dumps(secrets))],
    )
    ws.on_open = on_open
    ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
