from .nodes import VideoCombine
from .s3_utils import S3Handler

class EmProps_VideoCombine(VideoCombine):
    @classmethod
    def INPUT_TYPES(s):
        input_types = super().INPUT_TYPES()
        input_types["required"]["s3_prefix"] = ("STRING", {"default": ""})
        return input_types

    def combine_video(self, s3_prefix="", **kwargs):
        # Call parent class to handle video creation
        result = super().combine_video(**kwargs)
        
        # Get the filenames from the result
        save_output, filenames = result[0]
        
        if save_output and filenames:
            # Upload files to S3
            s3_handler = S3Handler()
            upload_results = s3_handler.upload_files(filenames, s3_prefix)
            
            # Add S3 URLs to the result if uploads were successful
            successful_urls = [url for success, url in upload_results if success]
            if successful_urls:
                print(f"Files uploaded to S3: {successful_urls}")
        
        return result
