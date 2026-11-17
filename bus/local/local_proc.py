import json
from prutil import message_is_valid, make_hyperparameters
from algo import AlteritBackMessage, AttackError
from . import LocalAttack

import time

async def process_message_local(m, logger, debug_err):
   """
   cast adversarial message and filter from initial image
   :param m: nats message with input data
   :param logger: logger for logging
   :param debug_err: pass to "Attack" object to output debugging information alongside algorythm running
   """
   try:
      data = m.data.decode() 
      parsed = json.loads(data)          
      valid, err = message_is_valid(parsed)
      if not(valid):
         error = "message validation error {}: ".format(err)
         logger.error(error)
         return AlteritBackMessage("", False, False, "", "", "", "", dict(), str(error),
                               ).serialize() 
      order_id = parsed.get('order_id')
      logger.debug("received a message with order_id %s", order_id)
   except json.JSONDecodeError:
      error = "invalid message format - json required"
      logger.error(error)
      return AlteritBackMessage("", False, False, "", "", "", "", dict(), str(error),
                               ).serialize() 
   
   # cast the hyperparameters for the attack workflow:
   try:
      algorythm = parsed.get('algorythm')
      alter_goal = parsed.get('alter_goal')
      params = make_hyperparameters(parsed)
      if debug_err:
         logger.debug("Actual hyperparameters: %s", json.dumps(params))
   except Exception as error:
      error = "invalid parsing"
      logger.error(error)
      return AlteritBackMessage("", False, False, "", "", "", "", dict(), str(error),
                                     ).serialize() 
   # cast the adversarial image and filter, generate attack and save adversarial image and filter to the storage
   try:
      a = LocalAttack(
            image_name=parsed.get('input_image_name'),
            save_filter=bool(parsed.get('save_filter')),
            debug_err=debug_err,
            logger=logger,
            algorythm=algorythm,            
            params = params,
            altergoal=alter_goal,
         ) 
      logger.debug("order %s: attack start, algorythm=%s save_filter=%r (raw=%r)",
                  order_id, algorythm, bool(parsed.get('save_filter')), parsed.get('save_filter'))
      a.generate_attack()
      logger.debug("order %s: attack done, saving images", order_id)
      a.save_final_image_to_storage()
      predictions = a.get_from_attack()
   except Exception as error:
      logger.error("order %s: attack/save failed: %s", order_id, error)
      return AlteritBackMessage(order_id, False, False, "", "", algorythm, alter_goal, dict(), str(error),
                                 ).serialize()
  
   return AlteritBackMessage(order_id, True, parsed.get('save_filter'), a.get_adv_name(), a.get_filter_name(),
                             algorythm, alter_goal, predictions,
                                 ).serialize()