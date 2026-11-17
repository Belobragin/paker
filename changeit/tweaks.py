"""main file for ML adversarial attack"""

import io
import json
import cv2
import numpy as np
import skimage.io
from PIL import Image

import tensorflow as tf
tf.compat.v1.logging.set_verbosity(tf.compat.v1.logging.ERROR)

from tensorflow.keras.optimizers import Adam
from tensorflow.keras.losses import (SparseCategoricalCrossentropy,
                                     CategoricalCrossentropy,
                                    )
from tensorflow.keras.applications.resnet50 import preprocess_input
from tensorflow.keras.applications import ResNet50
from tensorflow.keras.applications.resnet50 import decode_predictions

from prutil import (prepare_image_resnet50, 
                    local_get_class_idx, get_name_extension, get_all_labels, 
                    from_tensor_to_numpy_for_cv2image,
                    )

from algo.algoclass import AlteritAlgoName, AttackError

class Attack:
    """
    this class provides constructor and image attack methods
    """
    def __init__(self,
                 debug_err,
                 logger,
                 algorythm,
                 params: dict,               
                 altergoal = None, 
                 ):
        self.logger = logger
        self.model = ResNet50(weights="imagenet")
        self.debug_err = debug_err
        self.all_labels, self.imagenet_classes = get_all_labels()
        try:
            self._validate(algorythm, altergoal)
        except Exception as ee:
            raise ee
        try:
            self.resnet_image = prepare_image_resnet50(self.image_array)
            self.base_image = tf.constant(self.resnet_image, dtype=tf.float32)
        except Exception as ee:
            raise AttackError("image forrmat invalid: {}".format (ee))
        self.base_learning_rate = params["base_learning_rate_untarg"]
        self.base_eps = params['base_eps']
        # base_eps is on the 0..1 scale; base_image is 0..255
        self.eps_pixels = self.base_eps * 255.0
        self.steps = params["steps_untarg"]
        self.verbose_step = params["verbose_step_untarg"]
        self.alter_goal = altergoal if altergoal is not None else ""
        self.algo = algorythm
        self.input_image_name, self.mime = get_name_extension(self.message_image_name)
        self.adversarial_name = ""
        self.filter_name = ""   
        self.initial_size = self.image_array.shape
        self.targeted = False
        if self.algo == AlteritAlgoName.basic_iterative_targeted:
            self.targeted = True
            self.base_learning_rate = params["base_learning_rate_targ"]
            self.steps = params["steps_targ"]
            self.verbose_step = params["verbose_step_targ"]
        self.verbose = True if debug_err else False
        self._make_resnet_predictions()
        self.initial_class_idx = int(self.predict["n0"][2])
        
    
    def _make_resnet_predictions(self) ->dict:
        """
        outputs Resnet50 predictions dictionary for the 3 (three) most probable classes
        :param image_array:: np.array representation of the image, resized and expanded
        """
        predictions = self.model.predict(preprocess_input(self.resnet_image.astype("float32")))
        decoded_predictions = decode_predictions(predictions, top=3)[0]
        self.logger.info("decoded predictions %s", decoded_predictions)
        back_data = {}
        for i, (imagenet_id, label, prob) in enumerate(decoded_predictions):
            back_data["n" + str(i)] = (
                imagenet_id,
                label,
                str(self.imagenet_classes.get(label, None)),
                str(int(prob * 10000) / 100),
            )
        self.predict = back_data
        return        
        

    def _validate(self, algorythm, altergoal = None):
        correct_algo = False
        for _, v in vars(AlteritAlgoName).items():
            if algorythm == v:
                correct_algo = True
        if not(correct_algo):
            raise AttackError("invalid algorythm: {}".format(algorythm))
        if (algorythm == AlteritAlgoName.basic_iterative_targeted) and (altergoal not in self.all_labels):
            raise AttackError("targeted goal invalid")

        
    def _generate_adversary_delta_basic_iterative_untargeted(self):
        """
        generate delta for attack
        """
        sccLoss = SparseCategoricalCrossentropy()
        optimizer = Adam(learning_rate=self.base_learning_rate)
        delta = tf.Variable(tf.zeros_like(self.base_image), trainable=True)
        for step in range(0, self.steps):
            with tf.GradientTape() as tape:
                tape.watch(delta)
                adversary = preprocess_input(self.base_image + delta)
                predictions = self.model(adversary, training=False)
                originalLoss = -sccLoss(tf.convert_to_tensor([self.initial_class_idx]), predictions)
                totalLoss = originalLoss
                if self.verbose:
                    if step % self.verbose_step == 0:
                        self.logger.debug("step: {}, loss: {}...".format(step,
                                totalLoss.numpy()))
                gradients = tape.gradient(totalLoss, delta)
                optimizer.apply_gradients([(gradients, delta)])
                delta.assign(tf.clip_by_value(delta, 
                                            clip_value_min=-self.eps_pixels,
                                            clip_value_max=self.eps_pixels))        
        self._delta = delta
        return


    def _generate_adversary_delta_basic_iterative_targeted(self):
        """
        generate delta for attack
        """
        sccLoss = SparseCategoricalCrossentropy()
        optimizer = Adam(learning_rate=self.base_learning_rate)
        delta = tf.Variable(tf.zeros_like(self.base_image), trainable=True)
        for step in range(0, self.steps):
            with tf.GradientTape() as tape:
                tape.watch(delta)
                adversary = preprocess_input(self.base_image + delta)
                predictions = self.model(adversary, training=False)
                originalLoss = -sccLoss(tf.convert_to_tensor([self.initial_class_idx]), predictions)
                targetLoss = sccLoss(tf.convert_to_tensor([local_get_class_idx(self.alter_goal)]),
                    predictions)
                totalLoss = originalLoss + targetLoss             
                if self.verbose:
                    if step % self.verbose_step == 0:
                        self.logger.debug("step: {}, loss: {}...".format(step,
                                totalLoss.numpy()))
        
                gradients = tape.gradient(totalLoss, delta)
                optimizer.apply_gradients([(gradients, delta)])
                delta.assign(tf.clip_by_value(delta, 
                                            clip_value_min=-self.eps_pixels,
                                            clip_value_max=self.eps_pixels))        
        self._delta = delta
        return
            

    def _generate_attack_fgsm(self):
        """
        FGSM attack.
        Based upon: https://www.tensorflow.org/tutorials/generative/adversarial_fgsm
        """
        cLoss = CategoricalCrossentropy()
        num_classes = self.model.output_shape[-1]
        label = tf.one_hot(self.initial_class_idx, num_classes)
        label = tf.reshape(label, (1, num_classes))

        with tf.GradientTape() as tape:
            tape.watch(self.base_image)
            prediction = self.model(preprocess_input(self.base_image), training=False)
            loss = cLoss(label, prediction)
        gradient = tape.gradient(loss, self.base_image)        
        self._delta = self.eps_pixels*tf.sign(gradient)
        return


    def _generate_attack_basic(self): 
        """
        base iterative attack on imagenet classification
        """             
        # numpy.ndarray:
        adver_image = (self.base_image + self._delta).numpy().squeeze()        
        adver_image = np.clip(np.rint(adver_image), 0, 255).astype("uint8")
        dim = (self.initial_size[1], self.initial_size[0])
        self.adversarial = cv2.resize(adver_image, dim, interpolation=cv2.INTER_AREA)
        # adver_image = cv2.cvtColor(self.adversarial, cv2.COLOR_RGB2BGR)        
        # deltaNp = self._delta.numpy().squeeze()   # process tensor to numpy array, but
                                            # this is not an image itself - if we try to draw it,
                                            # we get black, since values are very small
        delta_image = from_tensor_to_numpy_for_cv2image(self._delta, from_1_to_255 = True) #.reshape(self.initial_size) #this is image
        delta_image = cv2.resize(delta_image, dim, interpolation=cv2.INTER_AREA)
        self.filtered = delta_image
        
        # predict on the image as stored (original size, encoded by file format), as an external reader sees it
        # without encode-decode - uncomment next line and comment 2 uncommented lines after commented:
        self.resnet_image = prepare_image_resnet50(adver_image)

        # to conform resnet50 predictions and predictions on a raw np.array - read `prediction_diff.md` at ./infov
        # stored_image = self._encode_decode(self.adversarial)
        # self.resnet_image = prepare_image_resnet50(stored_image)
        self._make_resnet_predictions()     
        return


    # def _encode_decode(self, array):
    #     """round-trip the array through the output file format, same as saving"""
    #     image_format = Image.registered_extensions()[f".{self.mime.lower()}"]
    #     buffer = io.BytesIO()
    #     Image.fromarray(array).save(buffer, format=image_format)
    #     buffer.seek(0)
    #     return np.array(skimage.io.imread(buffer))


    def _generate_output_test_data(self):
        """
        generate constant gray test images
        """
        gray_image = np.full(self.initial_size, 128, dtype=np.uint8)
        self.adversarial = gray_image.copy()
        self.filtered = gray_image.copy()
        return


    def generate_attack(self):
        """
        applies attack based on self.algo
        """
        try:
            if self.algo == vars(AlteritAlgoName)['test_algo']:
                self._generate_output_test_data()
            else:
                if self.algo == vars(AlteritAlgoName)['basic_iterative_untargeted']:
                    self._generate_adversary_delta_basic_iterative_untargeted()
                elif self.algo == vars(AlteritAlgoName)['basic_iterative_targeted']:
                    self._generate_adversary_delta_basic_iterative_targeted()
                elif self.algo == vars(AlteritAlgoName)['fgsm_algo']:
                    self._generate_attack_fgsm()
                else:
                    raise AttackError("strange unvalidated algorythm: {}".format(self.algo))
                self._generate_attack_basic()
            return
        except Exception:
            raise