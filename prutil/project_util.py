import os
import json
import cv2
import numpy as np
import requests
from pathlib import Path
from tensorflow import reduce_max, reduce_min

from .hyperparameters_default import (BASE_EPS, BASE_LEARNING_RATE_TARG, BASE_LEARNING_RATE_UNTARG,
                    STEPS_TARG, STEPS_UNTARG, VERBOSE_STEP_TARG, VERBOSE_STEP_UNTARG)

from algo.algoclass import AlteritAlgoName
import logging
logger = logging.getLogger(__name__)

def local_get_class_idx(label):
    """
    obtain imagenet id by label
    """
    labelPath = os.path.join(os.path.dirname(__file__),
                            "imagenet_class_index.json")
    with open(labelPath) as f:
        imageNetClasses = {labels[1]: int(idx) for (idx, labels) in
                        json.load(f).items()}
    return imageNetClasses.get(label, None)


def required_env(name, default=None):
    value = os.environ.get(name, default)
    if value is None or not value.strip():
        raise ValueError(f"{name} must be set to a non-empty value")
    return value


def message_is_valid(data: dict):
    """
    validate message format
    """
    
    if data.get('order_id',0) == 0:
        return False, "zero order_id"
    a = data.get('algorythm', "")
    if len(a) == 0:
        return False, "algorythm absent"
    if len(data.get('alter_goal', "")) == 0 and a == vars(AlteritAlgoName)["basic_iterative_targeted"]:
        return False, "alter goal absent for biterate targeted"
    return True, ""


def get_name_extension(name:str):
    """
    seperate file name and file extension
    """
    return name.split(".")[-2], name.split(".")[-1]


def get_all_labels() -> set:
    """
    outputs
    1) set of imagenet labels, say {"tench}, "goldfish", ...}
    2) dict with keys as labels and values as imagenet class number, say {"tench":0, "goldfish":1, ...}
    """    
    label_path = Path(__file__).resolve().parent / "imagenet_class_index.json"
    with label_path.open(encoding="utf-8") as file:
        try:
            imagenet_classifier = json.load(file)
        except Exception:
            raise
    output = set()
    imagenet_classes = dict()
    for idx, label in imagenet_classifier.items():
        output.add(label[1])
        imagenet_classes[label[1]] = int(idx)
    return output, imagenet_classes


# convert tensor to numpy array
def from_tensor_to_numpy_for_cv2image(tf_tens = None,
                                          from_1_to_255 = False
                                          ):
    """ generate np.array() to demonstrate image """
    if tf_tens is not None:
        tf_tens = tf_tens.numpy().squeeze()
        # cv2 range is 0...255, but we recieve perturbations in -1...1 range:
        if from_1_to_255:
            koeff_plus = reduce_max(tf_tens, axis=None) #
            koeff_minus = reduce_min(tf_tens, axis=None)
            tf_tens = 255*(tf_tens - koeff_minus)/(koeff_plus - koeff_minus)
        tf_tens = np.clip(tf_tens, 0, 255).astype("uint8")
        tf_tens = cv2.cvtColor(tf_tens, cv2.COLOR_RGB2BGR)        
    return tf_tens


def make_hyperparameters(parsed)->dict:
    """
    if hyperparameter is in the input, set its value;
    otherwise set default
    :param parsed: to add imput hyperparameter values, will take it from the input message
    """
    params = dict() 
    params["base_eps"] = parsed.get('base_eps', BASE_EPS)
    params["base_learning_rate_targ"] = parsed.get('base_learning_rate_targ', BASE_LEARNING_RATE_TARG)
    params["base_learning_rate_untarg"] = parsed.get('base_learning_rate_untarg', BASE_LEARNING_RATE_UNTARG)
    params["steps_targ"] =  parsed.get('steps_targ', STEPS_TARG)
    params["steps_untarg"] =  parsed.get('steps_untarg', STEPS_UNTARG)
    params["verbose_step_targ"] = parsed.get('verbose_step_targ', VERBOSE_STEP_TARG)
    params["verbose_step_untarg"] = parsed.get('verbose_step_untarg', VERBOSE_STEP_UNTARG)
    params["save_objects"] = parsed.get('save_objects', 0) 
    
    return params
    
    
    
        
        
    
