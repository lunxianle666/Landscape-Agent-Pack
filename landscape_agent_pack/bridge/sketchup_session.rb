# Inspect actual SketchUp entities. Results are written to an isolated JSON file.
require 'json'

module LandscapeAgentPack
  module SketchupSession
    module_function

    def mm_point(point)
      [point.x.to_mm, point.y.to_mm, point.z.to_mm]
    end

    def collect(entities, transform, edges, curves, depth = 0)
      raise 'Nested CAD reference deeper than 16' if depth > 16
      entities.each do |entity|
        case entity
        when Sketchup::Edge
          a = mm_point(entity.start.position.transform(transform))
          b = mm_point(entity.end.position.transform(transform))
          edges << {'a' => a, 'b' => b, 'tag' => entity.layer.name,
                    'curve_id' => entity.curve ? entity.curve.object_id : nil}
          curve = entity.curve
          if curve && !curves.key?(curve.object_id)
            row = {'id' => curve.object_id, 'class' => curve.class.name,
                   'edge_count' => curve.edges.length,
                   'vertices' => curve.vertices.map { |v| mm_point(v.position.transform(transform)) }}
            if curve.respond_to?(:center)
              row['center'] = mm_point(curve.center.transform(transform))
              row['radius_mm'] = curve.radius.to_mm if curve.respond_to?(:radius)
              row['start_angle_rad'] = curve.start_angle if curve.respond_to?(:start_angle)
              row['end_angle_rad'] = curve.end_angle if curve.respond_to?(:end_angle)
            end
            curves[curve.object_id] = row
          end
        when Sketchup::Group
          collect(entity.entities, transform * entity.transformation, edges, curves, depth + 1)
        when Sketchup::ComponentInstance
          collect(entity.definition.entities, transform * entity.transformation, edges, curves, depth + 1)
        end
      end
    end

    def snapshot(expected_path = nil)
      model = Sketchup.active_model
      raise 'Model path mismatch' if expected_path &&
        File.expand_path(model.path).tr('\\', '/').downcase != File.expand_path(expected_path).tr('\\', '/').downcase
      refs = model.entities.grep(Sketchup::ComponentInstance).select { |entity| entity.name == 'CAD_REFERENCE' }
      raise 'CAD_REFERENCE missing or duplicated' unless refs.length == 1
      ref = refs.first
      edges = []
      curves = {}
      collect(ref.definition.entities, ref.transformation, edges, curves)
      box = ref.bounds
      tags = model.layers.map(&:name)
      {
        'sketchup_version' => Sketchup.version,
        'model_path' => model.path,
        'model_units_code' => model.options['UnitsOptions']['LengthUnit'],
        'reference_name' => ref.name,
        'reference_type' => ref.typename,
        'reference_pid' => ref.persistent_id,
        'reference_tag' => ref.layer.name,
        'reference_visible' => ref.visible? && !ref.hidden?,
        'reference_transform' => ref.transformation.to_a,
        'reference_markers' => {
          'source_sha256' => ref.get_attribute('LAPBridge', 'source_sha256'),
          'source_format' => ref.get_attribute('LAPBridge', 'source_format'),
          'source_units' => ref.get_attribute('LAPBridge', 'source_units'),
          'bridge_mode' => ref.get_attribute('LAPBridge', 'bridge_mode'),
          'import_method' => ref.get_attribute('LAPBridge', 'import_method')
        },
        'root_entities' => model.entities.map { |e| {'type' => e.typename, 'name' => e.respond_to?(:name) ? e.name : '', 'tag' => e.layer.name} },
        'tags' => tags,
        'bbox_mm' => mm_point(box.min) + mm_point(box.max),
        'edge_count' => edges.length,
        'edges_by_tag' => edges.group_by { |e| e['tag'] }.transform_values(&:length),
        'edges' => edges,
        'curves' => curves.values
      }
    end

    def write_snapshot(path, expected_path = nil)
      raise 'Snapshot overwrite refused' if File.exist?(path)
      data = snapshot(expected_path)
      File.open(path, File::WRONLY | File::CREAT | File::EXCL, 0600) do |file|
        file.write(JSON.pretty_generate(data))
      end
      {'snapshot_path' => path, 'edge_count' => data['edge_count'],
       'bbox_mm' => data['bbox_mm'], 'tags' => data['tags'],
       'model_path' => data['model_path']}
    end
  end
end
