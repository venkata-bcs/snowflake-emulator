"""
Stage and cloud storage manager for Snowflake Emulator.
Supports Local directory stages and S3 / MinIO external stages.
"""

import glob
import hashlib
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse
import boto3
from botocore.client import Config

from snowflake_emulator.config import settings


class StageManager:
    def __init__(self):
        self.local_root = Path(settings.local_stage_dir).resolve()
        self.local_root.mkdir(parents=True, exist_ok=True)
        self._s3_client = None

    def _get_s3_client(self):
        if self._s3_client is None:
            self._s3_client = boto3.client(
                "s3",
                endpoint_url=settings.s3_endpoint_url,
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key,
                region_name=settings.aws_default_region,
                config=Config(s3={"addressing_style": "path"})
            )
        return self._s3_client

    def get_stage_local_dir(self, stage_name: str) -> Path:
        clean_name = stage_name.replace("@", "").replace("/", "_").strip()
        stage_dir = self.local_root / clean_name
        stage_dir.mkdir(parents=True, exist_ok=True)
        return stage_dir

    def list_stage_files(self, stage_name: str, stage_url: Optional[str] = None, pattern: Optional[str] = None) -> List[Dict[str, Any]]:
        results = []
        clean_stage = stage_name.replace("@", "").strip()
        
        if stage_url and (stage_url.startswith("s3://") or stage_url.startswith("s3a://")):
            # S3 / MinIO stage
            try:
                parsed = urlparse(stage_url)
                bucket = parsed.netloc
                prefix = parsed.path.lstrip("/")
                s3 = self._get_s3_client()
                resp = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)
                for obj in resp.get("Contents", []):
                    key = obj["Key"]
                    if pattern and not re.search(pattern, key):
                        continue
                    results.append({
                        "name": f"{clean_stage}/{key}",
                        "size": obj["Size"],
                        "md5": obj["ETag"].strip('"'),
                        "last_modified": obj["LastModified"].strftime("%a, %d %b %Y %H:%M:%S GMT")
                    })
            except Exception as e:
                # Fallback to local stage dir if S3 is not reachable locally
                pass

        # Also inspect local stage directory
        stage_dir = self.get_stage_local_dir(clean_stage)
        for filepath in stage_dir.rglob("*"):
            if filepath.is_file():
                rel_path = filepath.relative_to(stage_dir).as_posix()
                if pattern and not re.search(pattern, rel_path):
                    continue
                size = filepath.stat().st_size
                mtime = datetime.fromtimestamp(filepath.stat().st_mtime, timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")
                # Calculate md5
                md5 = hashlib.md5(filepath.read_bytes()).hexdigest()
                results.append({
                    "name": f"{clean_stage}/{rel_path}",
                    "size": size,
                    "md5": md5,
                    "last_modified": mtime
                })

        return results

    def get_file_for_ingest(self, stage_name: str, file_path: str, stage_url: Optional[str] = None) -> Path:
        """
        Retrieves a staged file and returns local path suitable for DuckDB COPY / read_csv.
        """
        clean_stage = stage_name.replace("@", "").strip()
        clean_file = file_path.replace(f"{clean_stage}/", "").strip()

        # Check local stage first
        local_target = self.get_stage_local_dir(clean_stage) / clean_file
        if local_target.exists():
            return local_target

        # Check S3 if url is provided
        if stage_url and (stage_url.startswith("s3://") or stage_url.startswith("s3a://")):
            parsed = urlparse(stage_url)
            bucket = parsed.netloc
            s3_key = f"{parsed.path.lstrip('/')}/{clean_file}".strip("/")
            local_target.parent.mkdir(parents=True, exist_ok=True)
            s3 = self._get_s3_client()
            s3.download_file(bucket, s3_key, str(local_target))
            return local_target

        raise FileNotFoundError(f"File '{file_path}' not found in stage '{stage_name}'")

    def save_staged_file(self, stage_name: str, filename: str, content: bytes) -> str:
        clean_stage = stage_name.replace("@", "").strip()
        stage_dir = self.get_stage_local_dir(clean_stage)
        target = stage_dir / filename
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        return str(target)
