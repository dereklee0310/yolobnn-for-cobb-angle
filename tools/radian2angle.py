import xml.etree.ElementTree as ET
import numpy as np
from pathlib import Path
import json

PREFIX = Path("./labelled_data")
FOLDS = ["f01", "f02", "f03"]
STARTS = [1, 21, 41]


def parse_xml(path):
    xml_data = ET.parse(path)
    root = xml_data.getroot()

    annotation_data = {
        "verified": root.attrib.get("verified"),
        "folder": root.find("folder").text,
        "filename": root.find("filename").text,
        "path": root.find("path").text,
        "size": {
            "width": int(root.find("size/width").text),
            "height": int(root.find("size/height").text),
            "depth": int(root.find("size/depth").text),
        },
        "segmented": int(root.find("segmented").text),
    }

    objects = []
    for obj in root.findall("object"):
        obj_data = {
            "type": obj.find("type").text,
            "name": obj.find("name").text,
            "pose": obj.find("pose").text,
            "truncated": int(obj.find("truncated").text),
            "difficult": int(obj.find("difficult").text),
            "robndbox": {
                "cx": float(obj.find("robndbox/cx").text),
                "cy": float(obj.find("robndbox/cy").text),
                "w": float(obj.find("robndbox/w").text),
                "h": float(obj.find("robndbox/h").text),
                "angle": float(obj.find("robndbox/angle").text),
            },
        }
        objects.append(obj_data)

    return {
        "annotation": annotation_data,
        "objects": objects,
    }


for fold, start in zip(FOLDS, STARTS):
    for id in range(start, start + 20):
        data = parse_xml(PREFIX / fold / "label" / f"00{id:02}.xml")

        radians = [x["robndbox"]["angle"] for x in data["objects"]]
        angles = list(map(lambda x: x * 180 / np.pi, radians))
        high90 = [(i, x) for i, x in enumerate(angles) if x > 90]
        low90 = [(i, x) for i, x in enumerate(angles) if x <= 90]

        if low90:
            max_idx, max_angle = max(low90, key=lambda x: x[1])
        else:
            max_idx, max_angle = max(high90, key=lambda x: x[1])

        if high90:
            min_idx, min_angle = min(high90, key=lambda x: x[1])
            min_angle -= 180
        else:
            min_idx, min_angle = min(low90, key=lambda x: x[1])

        result = {
            "max_idx": max_idx,
            "max": max_angle,
            "min_idx": min_idx,
            "min": min_angle,
            "diff": max_angle - min_angle,
        }
        print(id, result)
        Path(PREFIX / fold / "angle").mkdir(parents=True, exist_ok=True)
        with open(PREFIX / fold / "angle" / f"00{id:02}.json", "w") as file:
            json.dump(result, file)
