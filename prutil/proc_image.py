import cv2
import numpy as np


RESNET50_INPUT_DIMENSIONS = (224, 224)

def prepare_image_resnet50(input_image):
    """
    image preparation for Resnet50 input
    """	
    # input_image = cv2.cvtColor(self.input_image, cv2.COLOR_BGR2RGB)        
    image = cv2.resize(input_image, RESNET50_INPUT_DIMENSIONS, interpolation=cv2.INTER_AREA)
    image = np.expand_dims(image, axis=0)
    return image