import websocket
import json
import pika

try:
    import thread
except ImportError:
    import _thread as thread
import time


# Initiate rabbitmq connection
rabbit_conn = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = rabbit_conn.channel()
channel.queue_declare(queue="ingress_id-hash")


# Websocket callbacks
def on_message(ws, message):
    # Attempt to parse JSON
    try:
        # Decode and extract kill id/hash
        data = json.loads(message)
        kill_id = data['killmail_id']
        kill_hash = data['zkb']['hash']

        # Publish to internal queue
        channel.basic_publish(
            exchange="",
            routing_key="ingress_id-hash",
            body="%i:%s" % (kill_id, kill_hash)
        )
        print("Published kill to ingress_id-hash:", kill_id, kill_hash)
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
        print(args)
        ws.send('{"action":"sub", "channel":"killstream"}')
    thread.start_new_thread(run, ())


if __name__ == "__main__":
    #websocket.enableTrace(True)
    ws = websocket.WebSocketApp(
        "wss://zkillboard.com:2096",
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )
    ws.on_open = on_open
    ws.run_forever()