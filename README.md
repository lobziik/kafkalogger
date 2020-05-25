Confluent Kafka Logging Handler
=====================

Python logger handler which using [Confluent Kafka](https://github.com/confluentinc/confluent-kafka-python) client under the hood.

Temporary lives there. Will be moved to GH soon.



How to Use
----------

```python
import logging
from kafka_logger.handlers import KafkaLoggingHandler

KAFKA_BOOTSTRAP_SERVER = ('<hostname:port>')
KAFKA_CA = '<path_to_ca_cert>'
TOPIC = '<publish_topic>'

logger = logging.getLogger('MyCoolProject')

# Instantiate your kafka logging handler object
kafka_handler_obj = KafkaLoggingHandler(KAFKA_BOOTSTRAP_SERVER,
                                        TOPIC,
                                        ssl_cafile=KAFKA_CA)

logger.addHandler(kafka_handler_obj)
# Set logging level
logger.setLevel(logging.DEBUG)

logger.info('Happy Logging!')
```