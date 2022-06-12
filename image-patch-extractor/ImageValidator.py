import os 
import re
from typing import Tuple
from PIL import Image
from concurrent.futures import ThreadPoolExecutor, as_completed

class ImageValidator: 
    #FixME base64 is not the same as base64url change the regex to detect the file names. 
    def __init__(self) -> None:
        return 
    
    def get_files_list(directory: str , recursive: bool) -> list[str]: 
        """gets the list of file paths inside a directory and also its subdirectories if recursive is set to True 
        :param directory: The directory to get the it's files paths
        :type directory: str
        :param recursive: If it's set to True the function will return paths of all files in the given directory 
                and all its subdirectories
        :type recursive: bool
        :returns: list of files
        :rtype: list[str]
        """
        if recursive is True: 
            return [os.path.join(root , file) for root , dirs , files in os.walk(directory) for file in files]
        else:      
            return [os.path.join(directory , path) for path in os.listdir(directory)]

    def __allowed_type(file: str , allowed_types: list = []) -> bool: 
        """Returns True only if the given file path is from the allowed file types by the user 
        :param file: The file path needed to validate 
        :type file: str
        :param allowed_types: list of the allowed file types , leave empty if you want to allow any type 
        :type allowed_types: list
        :returns: True if the file type is within the allowed list 
        :rtype: bool
        """
        return True if len(allowed_types) == 0 else (os.path.splitext(file)[1] in allowed_types)

    def __validate_task(self, image: str,  min_size: tuple = (64, 64), allowed_types: list = []):
        
        try: 
            #try to open the image if it was corrupted it will return an exception 
            im = Image.open(image)
            _ , image_extension = os.path.splitext(image)
            
            #Check that the image is larger than min_size.
            if im.size[0] < min_size[0] or im.size[1] < min_size[1]: 
                return False, image 
            
            #check if the file extension matches the image format an exception is applied for jpeg and jpg files as they are the same
            if im.format is None or im.format.lower() != image_extension.lower()[1:]: 
                if not (image_extension.lower()[1:] == 'jpg' and im.format.lower() == 'jpeg'): 
                    #image is invalid because its extension doesn't match its format 
                    return False, image
    
            im.verify()
            return True, image
        except Exception: 
            #File is invalid because it's corrupted 
            return False, image 
     
    def validate(self, directory: str , min_size: tuple = (64, 64), recursive: bool = False , allowed_types = [], num_workers: int = 8) -> Tuple[list,list]:
        #FixME -> Add the steps of validation to be clear for the user. 
        """Validates all images contained in the path given with all it's subdirectories as well if recursive is true
        :param directory: The directory containing the files to be validated 
        :type directory: str
        :param min_size: min size of image dimension to be considered as valid image, comparison is made with on each dimension.  
        :type min_size: tuple
        :param recursive: If it's set to True the function will search and validate all images in 
                the given directory and all its subdirectories
        :type recursive: bool
        :param allowed_types: list of the allowed images extensions if it's empty then all image types will be considered 
        :type allowed_types: list
        :param num_workers: Number of threads to process the files.
        :type num_workers: int
        :returns: A tuple of two lists the first are the valid image paths and the other is for the invalid ones.
        :rtype: list[str]
        """
        
        #gets the whole files from the directory 
        files_list = ImageValidator.get_files_list(directory , recursive)
        #exclude only files 
        images_list = [file for file in files_list if ImageValidator.__allowed_type(file , allowed_types)]
        
        #List of invalid files to make the function return it
        failed_validation = set()
        valid_images = set() 
        #Remove any file that has non-base64 character as a file name 
        #Regular expression used to match strings containing only base64 chars 
        #FixME add options to exclude ASCII characters as well.
        regular_exp = re.compile(r'^[a-zA-Z0-9+/=]*$')
        [failed_validation.add(image) for image in images_list if regular_exp.fullmatch(os.path.splitext(os.path.split(image)[-1])[0]) is None]
        
        thread_pool = ThreadPoolExecutor(max_workers = num_workers)
        
        futures = [] 
        
        for image in images_list: 
            
            task = thread_pool.submit(self.__validate_task , image, min_size, allowed_types,)
            futures.append(task)
        
        for future in as_completed(futures): 
            try: 
                status, file_name = future.result()
                valid_images.add(file_name) if status else failed_validation.add(image)
            except Exception: 
                continue
            
            
        return (list(valid_images), list(failed_validation))
