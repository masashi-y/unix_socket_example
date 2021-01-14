import argparse
import socket
import sys

from message_pb2 import *
from utils import recv_msg, send_msg

parser = argparse.ArgumentParser()
parser.add_argument(
    "--FILENAME", type=str, default="/tmp/py_server", help="unix domain socket"
)
args = parser.parse_args()

texts = Texts(texts=[line.strip() for line in sys.stdin])
print(texts)

with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:

    s.connect(args.FILENAME)
    send_msg(s, texts.SerializeToString())
    results = Results.FromString(recv_msg(s))
    print(results)
