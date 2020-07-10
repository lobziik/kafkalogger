Confluent Kafka Logging Handler
=====================

Python logger handler which using [Confluent Kafka](https://github.com/confluentinc/confluent-kafka-python) client under the hood.
Check possible [configuration](https://github.com/edenhill/librdkafka/blob/master/CONFIGURATION.md) options, if necessary.


Inspired by [kafka-logging-hanlder](https://github.com/redhat-aqe/kafka-logging-handler) by redhat-aqe


Known issues and limitations
------------
 - In case of connection issues it will be reported to stdout via separate internal logger
 - Only `SSL` and `PLAINTEXT` security protocols was tested.

Installation
------------

The current stable release:

    pip install kafkalogger


Handler configuration options
---------------------

Argument                                 | type | Default | Description
-----------------------------------------|------|---------| --------------------------
**hosts_list** | list | | list of the Kafka hostnames
**topic** | str | | kafka consumer topic to where logs are forwarded
**security_protocol** | str (optional) | SSL | KafkaProducer security protocol
**ssl_cafile** | str | | path to CA file
**extended_producer_config** | dict (optional) | | extra parameters to update [confluent_kafka.SerializingProducer](https://docs.confluent.io/current/clients/confluent-kafka-python/#serde-producer) config
**additional_fields** | dict (optional) | | A dictionary with all the additional fields that you would like to add to the logs, such as application name
**log_preprocess** | list (with callables) (optional) | | list of functions, which will be applied to log record in provided order
**internal_logger_level** | str (optional) | INFO | internal logger loglevel
**delivery_timeout** | int (optional) | 2 | delivery timeout in seconds


Example usage
----------

```python
import logging
from kafkalogger.handlers import KafkaLoggingHandler

KAFKA_BOOTSTRAP_SERVER = ('<hostname:port>')
KAFKA_CA = '<path_to_ca_cert>'
TOPIC = '<publish_topic>'

logger = logging.getLogger('MyCoolProject')

# Instantiate your kafka logging handler object
kafka_handler_obj = KafkaLoggingHandler(
    KAFKA_BOOTSTRAP_SERVER,
    TOPIC,
    ssl_cafile=KAFKA_CA,
    extended_producer_config={}
)

logger.addHandler(kafka_handler_obj)
# Set logging level
logger.setLevel(logging.DEBUG)

logger.info('Happy Logging!')
```

or via dict config

```Python
{
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'kafka': {
            'level': 'DEBUG',
            'class': 'kafkalogger.handlers.KafkaLoggingHandler',
            'hosts_list': 'localhost',
            'security_protocol': 'SSL',
            'ssl_cafile': '/path/to/cafile.crt',
            'topic': 'service_logs',
            'additional_fields': {
                'service': 'my-cool-service'
            },
            'extended_producer_config': {}
        }
    },
    'loggers': {
        'django': {
            'level': 'INFO',
            'handlers': ['kafka'],
            'propagate': True,
        },
    }
}
```
