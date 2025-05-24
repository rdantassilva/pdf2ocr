from typing import Optional

class ProcessingConfig:
    log_path: Optional[str] = None
    workers: int = 2
    batch_size: Optional[int] = None 