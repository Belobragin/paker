import os
os.environ.setdefault("PYTHONDONTWRITEBYTECODE", "1")
os.environ.setdefault("TF_ENABLE_ONEDNN_OPTS", "0")
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")
# os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

import logging
import asyncio
from algo.algoclass import AttackError
from bus.local import process_message_local
from prutil import (required_env,
                    NatsCallbacks)



logger = logging.getLogger(__name__)

# debug_errors:
debug_error= False
debug_env = os.environ.get("DEBUG", "0")
if debug_env in {"true", "True", "1"}:
    debug_error= True

async def main():
    import nats

    nats_address = required_env("NATS_ADDRESS", "nats://127.0.0.1:4222")
    nats_name = required_env("NATS_AKER_NAME")
    nats_user = required_env("NATS_AKER_USER")
    nats_password = required_env("NATS_AKER_PSW")    

    nats_cb = NatsCallbacks(logger)
   
    try:
        nc = await nats.connect(
            servers=[nats_address],
            name=nats_name,
            user=nats_user,
            password=nats_password,
            allow_reconnect=True,
            reconnect_time_wait=5,
            max_reconnect_attempts=2,
            connect_timeout=5,
            ping_interval=3,
            max_outstanding_pings=2,
            error_cb=nats_cb.on_nats_error_callback,
            disconnected_cb=nats_cb.on_disconnected,
            reconnected_cb=nats_cb.reconnected_callback,
            closed_cb=nats_cb.closed_callback,
        )
    except Exception as error:
        logger.error("local NATS server is unavailable: %s", error)
        return
    
    logger.info("Connected to NATS as %s", nats_name)
    nats_cb.connected = True
    
    # recieve and log messages
    ch_from = required_env("NATS_FOR_PROCESSING_CHAN")
    ch_to = required_env("NATS_FROM_ALTERED_CHAN")
    try:
        sub = await nc.subscribe(ch_from)
        while True:
            msg = await sub.next_msg(timeout=None)            
            logger.info("received a message from input channel %s", msg)
            try:
                back_msg = await process_message_local(msg, logger, debug_error)                
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
            logger.info("processed adversarial message to ouput channel %s", back_msg)
            try:                
                await nc.publish(ch_to, back_msg)
            except Exception as error:
                if debug_error:
                   logger.exception("Unexpected error while publishing a message: %s", error) 
                else:                
                    logger.error("Unexpected error while publishing a message: %s", error)
                continue
    except asyncio.CancelledError:
        # Ctrl+C cancels the worker task; let finally close NATS quietly.
        logger.info("application now stops")
        pass
    finally:
        nats_cb.shutting_down = True
        try:
            await nc.flush()
        except Exception as error:
            logger.error("Server message flush error: %s", error)
        finally:
            await nc.close()
        
if __name__ == "__main__":
    log_level = os.environ.get("LOGGER_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=getattr(logging, log_level, logging.INFO),
        format="%(asctime)s %(levelname)s:%(name)s:%(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    except Exception as error:
        logger.fatal("application stops: %s", error)
    
