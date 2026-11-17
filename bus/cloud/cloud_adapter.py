
import io
import os
from functools import lru_cache
import boto3
import numpy as np
import skimage.io
from PIL import Image

from algo.algoclass import AttackError

from prutil import required_env, get_stack_output
from changeit import Attack


@lru_cache(maxsize=None)
def _bucket_name(stack_name, output_key):
    return get_stack_output(stack_name, output_key)


class CloudAttack(Attack):
    
    def __init__(self, image_name, save_filter, debug_err, logger, algorythm, params:dict, altergoal=None):
        self.save_filter = save_filter
        self.message_image_name = image_name
        resource_stack_name = os.environ["AWS_RESOURCE_CFN_WEREWOLF_STACK_NAME"]
        bucket_output_key = f"{os.environ['AWS_RESOURCE_PREFIX']}ProjectBucketName"
        self.image_storage_path = os.environ['IMAGE_CLOUD_STORAGE']
        self.adversarial_storage_path = os.environ['ADVERSARIAL_CLOUD_STORAGE']
        self.filter_storage_path = os.environ['FILTER_CLOUD_STORAGE']
        self.bucket_name = _bucket_name(resource_stack_name, bucket_output_key)
        self.project_bucket = boto3.resource('s3').Bucket(self.bucket_name)
        self.image_array = self.cast_image(image_name) 
        super().__init__(debug_err, logger, algorythm, params, altergoal)
    

    def cast_image(self, image_name):
        """
        convert s3 object to numpy array
        """          
        key = f"{self.image_storage_path}/{image_name}"
        body = self.project_bucket.Object(key).get()["Body"].read()
        return np.array(skimage.io.imread(io.BytesIO(body)))
    
    
    def _output_storage(self):
        """
        make attributes of self.adversarial_name and self.filter_name
        """
        try:
            alg_mark = ""
            if len(self.algo) >=20:
                alg_mark = self.algo[:20] + "."
            else:
                alg_mark = self.algo + "."          
            self.adversarial_name = (
                f"{self.adversarial_storage_path}/{self.input_image_name}_adversarial_{alg_mark}{self.mime}")
            if self.save_filter:
                self.filter_name = (
                    f"{self.filter_storage_path}/{self.input_image_name}_filter_{alg_mark}{self.mime}")
            return
        except AttackError as ee:
            raise ee
    

    def save_final_image_to_storage(self):
        """
        save casted adversarial and filter images to s3 object storage
        """        
        self._output_storage()
        self.logger.debug("save: save_filter=%r adversarial_name=%s filter_name=%s",
                         self.save_filter, self.adversarial_name, self.filter_name)
        try:    
            self._log_array("adversarial", self.adversarial)
            self._put_image(self.adversarial, self.adversarial_name)
            self._log_saved(self.adversarial_name)
            if self.save_filter:
                self._log_array("filter", self.filtered)
                self._put_image(self.filtered, self.filter_name)
                self._log_saved(self.filter_name)
            else:
                self.logger.debug("save: filter skipped, save_filter is falsy")
        except AttackError as ee:
            raise ee 
        except Exception:
            self.logger.error("save: failed to write image")
            raise  


    def _log_array(self, label, arr):
        self.logger.debug("save: %s array shape=%s dtype=%s min=%s max=%s", label,
                         getattr(arr, "shape", None), getattr(arr, "dtype", None),
                         arr.min() if arr is not None else None, arr.max() if arr is not None else None)


    def _put_image(self, array, key):
        """encode array by the file extension and upload it to the project bucket"""
        image_format = Image.registered_extensions()[f".{self.mime.lower()}"]
        buffer = io.BytesIO()
        Image.fromarray(array).save(buffer, format=image_format)
        self.project_bucket.Object(key).put(Body=buffer.getvalue())


    def _log_saved(self, key):
        """log the object as seen in the bucket after upload"""
        try:
            size = self.project_bucket.Object(key).content_length
            self.logger.debug("save: written s3://%s/%s size=%d bytes", self.bucket_name, key, size)
        except Exception:
            self.logger.error("save: object NOT found after upload s3://%s/%s", self.bucket_name, key)
            raise
    
    
    def get_adv_name(self):
        """
        output adversarial file name
        """
        
        return self.adversarial_name
    
        
    def get_filter_name(self):
        """
        output filter file name
        """
        
        return self.filter_name
    
    def get_from_attack(self):
        """
        output alter_goal and predctions for the adversarial image
        """
        return self.predict
        