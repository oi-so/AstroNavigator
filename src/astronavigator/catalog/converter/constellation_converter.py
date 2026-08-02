from __future__ import annotations

import json
from pathlib import Path


from astronavigator.catalog.converter.converter import CatalogConverter


CONSTELLATION_LABELS_PATH = Path(Path.cwd() / "data" / "constellation_label.json")



class ConstellationConverter(CatalogConverter):
    def convert(self, source: str) -> str:
        constellations = []
        with open(CONSTELLATION_LABELS_PATH, "r", encoding="utf-8") as f:
            constellation_labels = json.load(f)
        
        for line in source.strip().splitlines():
            tokens = line.strip().split()
            if not tokens:
                continue
                
            name = tokens[0]
            # num_lines = int(tokens[1])
            hip_ids = tokens[2:]
            
            lines = []
            for i in range(0, len(hip_ids), 2):
                if i + 1 < len(hip_ids):
                    lines.append({
                        "from": hip_ids[i],
                        "to": hip_ids[i + 1]
                    })
            
            constellations.append({
                "name": name,
                "lines": lines,
                "ra_deg": constellation_labels.get(name, {}).get("ra_deg"),
                "dec_deg": constellation_labels.get(name, {}).get("dec_deg")
            })

        return json.dumps(constellations, indent=2, ensure_ascii=False)