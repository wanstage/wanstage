import logging
import os

import yaml

log = logging.getLogger(__name__)


def safe_load_brand_config(path="config/brand_config.yaml"):
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(base_dir)
        abs_path = os.path.join(project_root, path)
        with open(abs_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return data
    except FileNotFoundError:
        log.error("brand_config not found")
        return {}
    except Exception as ex:
        log.error("brand_config load error: %s", ex)
        return {}
