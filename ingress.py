import websocket
import json

try:
    import thread
except ImportError:
    import _thread as thread
import time

from hydration.tasks import parse_killmail


# Websocket callbacks
def on_message(ws, message):
    # Attempt to parse JSON
    try:
        # Decode and extract kill id/hash
        data = json.loads(message)
        kill_id = data['killmail_id']
        kill_hash = data['zkb']['hash']

        parse_killmail.delay(kill_id, kill_hash)
        print("Queued Killmail Parse", kill_id, kill_hash)
    except json.decoder.JSONDecodeError:
        print("Error occurred decoding the JSON in a message")
    except KeyError:
        print("An error occurred getting the key from the decoded package")


def on_error(ws, error):
    print(error)


def on_close(ws, error):
    print("Websocket Closed")


def on_open(ws):
    def run(*args):
        print("Connected to Zkillboard websocket server, sending killstream listen action")
        ws.send('{"action":"sub", "channel":"killstream"}')
    thread.start_new_thread(run, ())


if __name__ == "__main__":
    # Connect websocket
    ws = websocket.WebSocketApp(
        "wss://zkillboard.com:2096",
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )
    ws.on_open = on_open
    ws.run_forever()