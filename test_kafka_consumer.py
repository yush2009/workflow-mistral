import sys
import logging as log
log.basicConfig(level=log.DEBUG)

from pykafka import KafkaClient

def main(host):
    print "Conneting kafka " + host + "..."
    client = KafkaClient(hosts=host)
    client.topics
    topic = client.topics[b'mistral']

    consumer = topic.get_simple_consumer(
        consumer_group=b'test1',
        auto_commit_enable=True,
        auto_commit_interval_ms=1,
        consumer_id=b'test')

    for message in consumer:
        if message is not None:
            print message.value


if __name__ == "__main__":
    if len(sys.argv) > 1:
        host = sys.argv[1]
    else:
        host = "124.127.116.223"

    main(host)
