
                            
from .local import process_message_local
from .cloud import process_message_cloud

__all__ = ["process_message_local",
           "process_message_cloud",
          ]
