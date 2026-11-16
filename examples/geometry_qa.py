"""Run with python -m examples.geometry_qa from the repository root."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory

import ezdxf

from landscape_agent_pack.cad.geometry_qa import GeometryProfile, analyze_dxf


def main():
    with TemporaryDirectory(prefix="lap-example-") as directory:
        source = Path(directory) / "景观 示例.dxf"
        doc = ezdxf.new(units=4)  # millimetres
        doc.layers.new("L-SITE")
        doc.modelspace().add_lwpolyline(
            [(0, 0), (1000, 0), (1000, 500), (0, 500)],
            close=True, dxfattribs={"layer": "L-SITE"},
        )
        doc.saveas(source)
        result = analyze_dxf(source, GeometryProfile(
            required_layers=("L-SITE",), closed_layers=("L-SITE",),
            expected_entity_count=1, allowed_bbox=(0, 0, 1000, 500),
        ))
    result.finish()
    print(json.dumps(result.to_dict(), ensure_ascii=True, indent=2))
    return result.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
