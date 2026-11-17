""" classes define algorythms for recognition and alter """
from datetime import datetime
import json


# project-specific errors
class AttackError(Exception):
    """AttackError is specific project error """
    pass

from enum import Enum

# any other algorythm but those in the AlteritAlgoName class - raises AttackError
class AlteritAlgoName(str, Enum):
    """algorythms to change image (attack) """
    # Basic iterative algorythm - targeted to some imageclass
    basic_iterative_targeted = 'biterate_targeted'
    # Basic iterative algorythm - untargeted
    basic_iterative_untargeted = 'biterate_untargeted'
    # Google suggested fast gradient sign method attack algorythm
    fgsm_algo = 'fgsm'
    # testing lightweight option, no real image processing
    test_algo = 'test_algo'
    
# return message
class AlteritBackMessage:
    """ this object is serialized and published """
    def __init__(self,
                order_id,
                success_adversarial,
                success_filter,
                adversarial_name,
                filter_name,
                algorythm:str,
                alter_goal:str,
                predictions:dict,
                error = None,             
                ):
        self.order_id = order_id
        self.success_adversarial = success_adversarial
        self.success_filter = success_filter
        self.adversarial_name = adversarial_name
        self.filter_name = filter_name
        self.error = error if error is not None else ""
        self.algorythm = algorythm
        self.alter_goal = alter_goal
        self.predictions = predictions
        
    def serialize(self):
        d = dict()
        d["order_id"] = self.order_id
        d["success_adversarial"] = self.success_adversarial
        d["success_filter"] = self.success_filter
        d["adversarial_name"] = self.adversarial_name
        if self.success_filter:
            d["filter_name"] = self.filter_name
        d["timestamp"] =  datetime.now().isoformat()
        d["error"] = self.error
        d["algorythm"] = self.algorythm
        d["alter_goal"] = self.alter_goal
        d["predictions"] = self.predictions
        return json.dumps(d).encode()
    