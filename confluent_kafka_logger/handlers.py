"""This module contains logging handler which forwards logs to Kafka."""
import datetime
import json
import logging
import socket
import sys

from confluent_kafka import SerializingProducer
from confluent_kafka.serialization import StringSerializer

from .exceptions import KafkaLoggerException


class KafkaLoggingHandler(logging.Handler):
    """
    This handler enables the user to forward logs to Kafka.

    Attributes:
        additional_fields (dict): extra fields attached to logs
        kafka_topic_name (str): topic name
        producer (kafka.KafkaProducer): producer object
    """

    __LOGGING_FILTER_FIELDS = ["msecs", "relativeCreated", "levelno", "created"]

    def __init__(
        self,
        hosts_list,
        topic,
        security_protocol="SSL",
        ssl_cafile=None,
        extended_producer_config=None,
        additional_fields=None,
        log_preprocess=None,
        internal_logger_level="INFO",
    ):
        """
        Initialize the handler.

        Args:
            hosts_list: list of the Kafka hostnames
            topic: kafka consumer topic to where logs are forwarded
            security_protocol (str, optional): KafkaProducer security protocol
            ssl_cafile (None, optional): path to CA file
            extended_producer_config (None, optional):
                extra arguments to update confluent_kafka.SerializingProducer config
            additional_fields (None, optional):
                A dictionary with all the additional fields that you would like
                to add to the logs, such the application, environment, etc.
            log_preprocess (None/list, optional):
                list of functions, handler will send the following to Kafka
                ...preprocess[1](preprocess[0](raw_log))...
            internal_logger_level (str, optional):
                internal logger loglevel.

        Raises:
            KafkaLoggerException: in case of incorrect logger configuration

        """

        self._internal_logger = self._init_internal_logger(internal_logger_level)

        self.log_preprocess = log_preprocess or []

        self.additional_fields = additional_fields or {}
        self.additional_fields.update(
            {"host": socket.gethostname(), "host_ip": socket.gethostbyname(socket.gethostname())}
        )

        if security_protocol == "SSL" and ssl_cafile is None:
            raise KafkaLoggerException("SSL CA file isn't provided.")
        self.kafka_topic_name = topic
        extended_producer_config = extended_producer_config or {}
        producer_config = {
            "bootstrap.servers": hosts_list,
            "security.protocol": security_protocol,
            "ssl.ca.location": ssl_cafile,
            "key.serializer": StringSerializer("utf_8"),
            "value.serializer": lambda msg, _: json.dumps(msg).encode("utf-8"),
            "delivery.timeout.ms": 4000,
            "error_cb": self.error_callback,
        }
        producer_config.update(extended_producer_config)

        self.producer = SerializingProducer(producer_config)

        logging.Handler.__init__(self)
        self._internal_logger.debug(f"KAFKA LOGGER INITIALIZED WITH CONFIG: {str(producer_config)}")

    @staticmethod
    def _init_internal_logger(level="INFO"):
        internal_handler = logging.StreamHandler(sys.stdout)
        internal_handler.setLevel(level)
        internal_handler.setFormatter(
            logging.Formatter("[%(asctime)s] [%(process)s] [%(name)s] [%(levelname)s]: %(message)s")
        )
        internal_logger = logging.getLogger("confluent_kafka_handler")
        internal_logger.addHandler(internal_handler)
        internal_logger.setLevel(level)
        internal_logger.propagate = False
        return internal_logger

    def prepare_record_dict(self, record):
        """
        Prepare a dictionary log item.

        Format a log record and extend dictionary with default values.

        Args:
            record (logging.LogRecord): log record

        Returns:
            dict: log item ready for Kafka
        """
        # use default formatting
        # Update the msg dict to include all of the message attributes
        self.format(record)

        # If there's an exception, let's convert it to a string
        if record.exc_info:
            record.msg = repr(record.msg)
            record.exc_info = repr(record.exc_info)

        # Append additional fields
        rec = self.additional_fields.copy()
        for key, value in record.__dict__.items():
            if key not in self.__LOGGING_FILTER_FIELDS:
                if key == "args":
                    # convert ALL argument to a str representation
                    # Elasticsearch supports number datatypes
                    # but it is not 1:1 - logging "inf" float
                    # causes _jsonparsefailure error in ELK
                    value = tuple(repr(arg) for arg in value)
                if key == "msg" and not isinstance(value, str):
                    # msg contains custom class object
                    # if there is no formatting in the logging call
                    value = str(value)
                rec[key] = "" if value is None else value
            if key == "created":
                # inspired by: cmanaha/python-elasticsearch-logger
                created_date = datetime.datetime.utcfromtimestamp(record.created)
                rec["timestamp"] = "{!s}.{:03d}Z".format(
                    created_date.strftime("%Y-%m-%dT%H:%M:%S"), int(created_date.microsecond / 1000)
                )
        # apply preprocessor(s)
        for preprocessor in self.log_preprocess:
            rec = preprocessor(rec)

        return rec

    def emit(self, record):
        """
        Prepare and send LogRecord to kafka topic

        Args:
            record: Logging message
        """
        record_dict = self.prepare_record_dict(record)
        self.producer.produce(
            self.kafka_topic_name, value=record_dict, on_delivery=self.error_callback
        )

    def error_callback(self, err, msg=None):
        if err:
            self._internal_logger.warning(err)
        if msg:
            self._internal_logger.debug(msg)

    def flush(self):
        if hasattr(self, "producer"):
            self.producer.flush()

    def close(self):
        """Close the handler."""
        logging.Handler.close(self)
