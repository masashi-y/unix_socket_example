import argparse
import logging
import multiprocessing
import os
import socket
import sys

from transformers import pipeline

from message_pb2 import *
from utils import recv_msg, send_msg

logger = logging.getLogger(__name__)


def daemonize():
    def fork():
        if os.fork():
            sys.exit()

    def throw_away_io():
        stdin = open(os.devnull, "rb")
        stdout = open(os.devnull, "ab+")
        stderr = open(os.devnull, "ab+", 0)

        for (null_io, std_io) in zip(
            (stdin, stdout, stderr), (sys.stdin, sys.stdout, sys.stderr)
        ):
            os.dup2(null_io.fileno(), std_io.fileno())

    fork()
    os.setsid()
    fork()
    throw_away_io()


def on_other_process(sock, model):
    message = Texts.FromString(recv_msg(sock))
    for text in message.texts:
        logger.info(f"input: {text}")
    results = Results(
        results=[Result(**prediction) for prediction in model(list(message.texts))]
    )
    logger.info("sending")
    send_msg(sock, results.SerializeToString())
    sock.close()
    logger.info("done")


def main(args):

    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
            s.bind(args.FILENAME)

            logger.info("loading sentiment analysis model")
            model = pipeline("sentiment-analysis")
            logger.info("done")

            if args.daemon:
                daemonize()

            while True:
                logger.info("listening")
                s.listen(5)
                connection, _ = s.accept()
                logger.info("receiving")
                on_other_process(connection, model)

    except KeyboardInterrupt:
        os.unlink(args.FILENAME)


if __name__ == "__main__":

    logging.basicConfig(
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
        level=logging.INFO,
    )

    parser = argparse.ArgumentParser()
    parser.add_argument("--daemon", action="store_true")
    parser.add_argument(
        "--FILENAME", type=str, default="/tmp/py_server", help="unix domain socket"
    )

    args = parser.parse_args()
    main(args)
