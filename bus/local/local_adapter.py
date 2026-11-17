
import os
import numpy as np
import skimage.io
from PIL import Image

from algo.algoclass import AttackError

from prutil import required_env
from changeit import Attack


class LocalAttack(Attack):
    
    def __init__(self, image_name, save_filter, debug_err, logger, algorythm, params:dict, altergoal=None):
        self.message_image_name = image_name
        self.image_array = self.cast_image(image_name)
        self.save_filter = save_filter
        super().__init__(debug_err, logger, algorythm, params, altergoal)
    
    @staticmethod    
    def cast_image(image_name):
        """
        convert file or object to numpy array
        """
        try:
            dir_path = required_env("IMAGE_LOCAL_STORAGE")
            filename = os.path.join(dir_path, image_name)
            if not(os.path.isfile(filename)):
                raise FileNotFoundError(f"image file not found: {filename}")
            im = skimage.io.imread(filename)            
            return np.array(im)
        except AttackError as ee:
            raise ee
    
    
    def _output_storage(self):
        """
        make attributes of self.adversarial_name and self.filter_name
        """
        try:        
            adversarial_path = required_env("ADVERSARIAL_LOCAL_STORAGE")
            alg_mark = ""
            if len(self.algo) >=20:
                alg_mark = self.algo[:20] + "."
            else:
                alg_mark = self.algo + "."          
            self.adversarial_name = os.path.join(adversarial_path, self.input_image_name + "_adversarial_" + alg_mark + self.mime)
            if self.save_filter:
                filter_path = required_env("FILTER_LOCAL_STORAGE")
                self.filter_name = os.path.join(filter_path, self.input_image_name + "_filter_" + alg_mark + self.mime)
            return
        except AttackError as ee:
            raise ee
    

    def save_final_image_to_storage(self):
        """
        save casted adversarial and filter images to file (object) storage
        """        
        self._output_storage()
        self.logger.debug("save: save_filter=%r adversarial_name=%s filter_name=%s",
                         self.save_filter, self.adversarial_name, self.filter_name)
        try:    
            self._log_array("adversarial", self.adversarial)
            Image.fromarray(self.adversarial).save(self.adversarial_name)
            self._log_saved(self.adversarial_name)
            if self.save_filter:
                self._log_array("filter", self.filtered)
                Image.fromarray(self.filtered).save(self.filter_name)
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


    def _log_saved(self, path):
        """log the result of the write as seen from inside the container"""
        directory = os.path.dirname(path)
        if os.path.isfile(path):
            self.logger.debug("save: written %s size=%d bytes, dir writable=%s", path,
                             os.path.getsize(path), os.access(directory, os.W_OK))
        else:
            self.logger.error("save: file NOT found after save %s (dir exists=%s, writable=%s, uid=%d)",
                              path, os.path.isdir(directory), os.access(directory, os.W_OK), os.getuid())
    
    
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
        