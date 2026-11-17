import os
os.environ.setdefault("PYTHONDONTWRITEBYTECODE", "1")
os.environ.setdefault("TF_ENABLE_ONEDNN_OPTS", "0")
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")

import logging
import asyncio
import signal
import sys
import boto3
from algo.algoclass import AttackError
from bus.cloud import process_message_cloud
from prutil import required_env, get_stack_output


logger = logging.getLogger(__name__)

# debug_errors:
debug_error= False
debug_env = os.environ.get("DEBUG", "0")
if debug_env in {"true", "True", "1"}:
    debug_error= True

async def main():
    stack_name = required_env("AWS_RESOURCE_CFN_WEREWOLF_STACK_NAME")
    prefix = required_env("AWS_RESOURCE_PREFIX")
    in_key = required_env("AWS_SQS_FOR_PROCESSING_CHAN", f"{prefix}SqsQueueName")
    out_key = required_env("AWS_SQS_RESULT_CHAN", f"{prefix}SqsResultQueueName")
    visibility_timeout = int(required_env("SQS_VISIBILITY_TIMEOUT", "1800"))

    try:
        sqs = boto3.client("sqs")
        queue_from = sqs.get_queue_url(QueueName=get_stack_output(stack_name, in_key))["QueueUrl"]
        queue_to = sqs.get_queue_url(QueueName=get_stack_output(stack_name, out_key))["QueueUrl"]
    except Exception as error:
        logger.error("cloud SQS queues are unavailable: %s", error)
        sys.exit(1)

    logger.info("Listening to SQS queue %s, results go to %s", queue_from, queue_to)

    # ECS sends SIGTERM on stop: finish the current message, then leave the loop
    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, stop.set)

    try:
        while not stop.is_set():
            resp = await asyncio.to_thread(
                sqs.receive_message,
                QueueUrl=queue_from,
                MaxNumberOfMessages=1,
                WaitTimeSeconds=20,
                VisibilityTimeout=visibility_timeout,
            )
            for msg in resp.get("Messages", []):
                logger.info("received a message from input queue %s", msg["MessageId"])
                try:
                    back_msg = await process_message_cloud(msg["Body"], logger, debug_error)
                except AttackError as error:
                    if debug_error:
                        logger.exception("Message processing failed: %s", error)
                    else:
                        logger.error("Message processing failed: %s", error)
                    continue
                except Exception as error:
                    if debug_error:
                        logger.exception("Unexpected error while processing a message: %s", error)
                    else:
                        logger.error("Unexpected error while processing a message: %s", error)
                    continue
                logger.info("processed adversarial message to output queue %s", back_msg)
                try:
                    await asyncio.to_thread(sqs.send_message, QueueUrl=queue_to, MessageBody=back_msg.decode())
                    await asyncio.to_thread(sqs.delete_message, QueueUrl=queue_from,
                                            ReceiptHandle=msg["ReceiptHandle"])
                except Exception as error:
                    # not deleted: the message returns to the queue after the visibility timeout
                    if debug_error:
                        logger.exception("Unexpected error while publishing a message: %s", error)
                    else:
                        logger.error("Unexpected error while publishing a message: %s", error)
                    continue
        logger.info("stop signal received, application now stops")
    except asyncio.CancelledError:
        logger.info("application now stops")

if __name__ == "__main__":
    log_level = os.environ.get("LOGGER_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=getattr(logging, log_level, logging.INFO),
        format="%(asctime)s %(levelname)s:%(name)s:%(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    # if not(debug_error):
    #     for noisy in ("boto3", "botocore", "s3transfer", "urllib3"):
    #         logging.getLogger(noisy).setLevel(logging.WARNING)
    for noisy in ("boto3", "botocore", "s3transfer", "urllib3"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    except Exception as error:
        logger.fatal("application stops: %s", error)
        sys.exit(1)
    
