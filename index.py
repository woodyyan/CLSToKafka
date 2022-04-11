#!/usr/bin/env python
# -*- coding: utf-8 -*-
import base64
import gzip
import logging
import os
import time

from kafka import KafkaProducer
from kafka.errors import KafkaError

logger = logging.getLogger('kafka')
logger.setLevel(logging.INFO)


class ClsToKafka(object):
    """
    CLS to kafka
    """

    def __init__(self, host, **kwargs):
        self.host = host

        self.producer = KafkaProducer(
            bootstrap_servers=[self.host],
            retries=10,
            max_in_flight_requests_per_connection=1,
            request_timeout_ms=30000,
            max_block_ms=60000,
            **kwargs
        )

    def send(self, topic, records):

        global count
        count = 0

        def on_send_success(record_metadata):
            global count
            count = count + 1

        def on_send_error(excp):
            logger.error('failed to send message', exc_info=excp)

        s_time = time.time()
        try:
            for record in records:
                key = ""
                # 当 key 为 "" 或者为 "None" 时，要传入key=None，这样python kafka库会随机选取一个partition写入消息
                if key == "" or key == "None":
                    key = None
                value = record

                # process the message if need
                # value = deal_message(data)

                self.producer.send(topic, key=key, value=value).add_callback(on_send_success).add_errback(on_send_error)

            # block until all async messages are sent
            self.producer.flush()
        except KafkaError as e:
            return e
        finally:
            if self.producer is not None:
                self.producer.close()
        e_time = time.time()

        return "{} messages delivered in {}s".format(count, e_time - s_time)


# process the message if need
def deal_message(message):
    return message


def main_handler(event, context):
    logger.debug("start main_handler")
    logger.info(event)

    kafka_address = os.getenv("kafka_address")
    kafka_topic_name = os.getenv("kafka_topic_name")

    kafka_to_kafka = ClsToKafka(
        kafka_address
        # security_protocol = "SASL_PLAINTEXT",
        # sasl_mechanism = "PLAIN",
        # sasl_plain_username = "ckafka-80o10xxx#lkoxx",
        # sasl_plain_password = "123",
        # api_version=(0, 10, 2)
    )
    debase = base64.b64decode(event['clslogs']['data'])
    data = gzip.decompress(debase).decode()
    print(data)

    ret = kafka_to_kafka.send(kafka_topic_name, data)
    logger.info(ret)
    return ret
