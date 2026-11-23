"""Check this local snapshot without any network access or third-party library."""
import gzip
import hashlib
import json
import struct
from pathlib import Path


def main():
    root = Path(__file__).resolve().parent
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    paths = set()
    for obj in manifest["objects"]:
        path = (root / obj["path"]).resolve()
        if not path.is_relative_to(root) or obj["path"] in paths:
            raise ValueError("Unsafe or duplicate object path")
        paths.add(obj["path"])
        stored = path.read_bytes()
        if (len(stored) != obj["stored_bytes"] or
                hashlib.sha256(stored).hexdigest() != obj["stored_sha256"]):
            raise ValueError("Stored bytes mismatch: " + obj["path"])
        content = gzip.decompress(stored) if path.suffix == ".gz" else stored
        if (len(content) != obj["uncompressed_bytes"] or
                hashlib.sha256(content).hexdigest() != obj["uncompressed_sha256"]):
            raise ValueError("Uncompressed bytes mismatch: " + obj["path"])
        if obj["format"] == "jnnw":
            if content[:4] != b"JNNW":
                raise ValueError("Invalid JNNW signature")
            count = struct.unpack_from("<I", content, 4)[0]
            if len(content) != 8 + 38 * count or count != obj["record_count"]:
                raise ValueError("Invalid JNNW count or size")
    objects = {obj["path"]: obj for obj in manifest["objects"]}
    for source in manifest["sources"]:
        obj = objects[source["object_path"]]
        if source["uncompressed_sha256"] != obj["uncompressed_sha256"]:
            raise ValueError("Invalid source mapping")
    print(json.dumps({"verified_objects": len(paths),
                      "source_objects": len(manifest["sources"]),
                      "stored_bytes": sum(o["stored_bytes"] for o in objects.values()),
                      "errors": 0}))


if __name__ == "__main__":
    main()
