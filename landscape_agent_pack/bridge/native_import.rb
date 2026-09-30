# SketchUp 2023 native CAD importer. This file never parses or redraws CAD.
require 'json'
require 'digest'

module LandscapeAgentPack
  module NativeImport
    module_function

    def normalized(path)
      File.expand_path(path).tr('\\', '/').downcase
    end

    def inside?(path, root)
      p = normalized(path)
      r = normalized(root).sub(%r{/+$}, '')
      p.start_with?(r + '/')
    end

    def run(request_file)
      request = JSON.parse(File.read(request_file, encoding: 'UTF-8'))
      root = request.fetch('workspace')
      source = request.fetch('source_cad')
      startup = request.fetch('startup_model')
      output = request.fetch('output_skp')
      raise 'Workspace path mismatch' unless inside?(request_file, root) &&
        [source, startup, output].all? { |p| inside?(p, root) }
      raise 'Source file missing' unless File.file?(source)
      raise 'Unsupported CAD format' unless %w[dwg dxf].include?(request.fetch('source_format')) &&
        File.extname(source).downcase == '.' + request.fetch('source_format')
      raise 'Existing SKP output refused' if File.exist?(output)
      raise 'Unit mismatch: CAD and SketchUp must be millimetres' unless
        request.fetch('source_units') == 'mm' && request.fetch('source_insunits') == 4 &&
        request.fetch('expected_su_units') == 'mm'
      raise 'CAD source hash mismatch' unless Digest::SHA256.file(source).hexdigest == request.fetch('source_sha256')
      raise 'Origin and CAD layers must be preserved' unless request.fetch('preserve_origin') &&
        request.fetch('tag_handling') == 'PRESERVE_CAD_LAYERS'

      model = Sketchup.active_model
      raise 'Active SketchUp model is not the automation-owned startup copy' unless normalized(model.path) == normalized(startup)
      raise 'SketchUp model has an open editing context' unless model.active_path.nil?
      before = { 'root_entities' => model.entities.length, 'definitions' => model.definitions.length }
      # Only this isolated startup copy is modified. Template figures are not CAD.
      model.entities.to_a.each(&:erase!)
      model.options['UnitsOptions']['LengthUnit'] = Length::Millimeter
      options = {
        :show_summary => false,
        :preserve_origin => true,
        :merge_coplanar_faces => request.fetch('merge_coplanar_faces'),
        :import_materials => request.fetch('import_materials')
      }
      definition = model.definitions.import(source, options)
      raise 'BLOCKED_NATIVE_IMPORT: native DefinitionList#import returned nil' unless definition
      raise 'BLOCKED_NATIVE_IMPORT: native CAD definition is empty' if definition.entities.length == 0
      reference = model.entities.add_instance(definition, Geom::Transformation.new)
      reference.name = 'CAD_REFERENCE'
      reference.layer = model.layers.add('CAD_REFERENCE')
      reference.set_attribute('LAPBridge', 'source_sha256', request.fetch('source_sha256'))
      reference.set_attribute('LAPBridge', 'source_format', request.fetch('source_format'))
      reference.set_attribute('LAPBridge', 'source_units', request.fetch('source_units'))
      reference.set_attribute('LAPBridge', 'bridge_mode', request.fetch('bridge_mode'))
      reference.set_attribute('LAPBridge', 'import_method', 'Sketchup::DefinitionList#import')
      {
        'native_import_executed' => true,
        'method' => 'Sketchup::DefinitionList#import',
        'source' => source,
        'options' => options.transform_keys(&:to_s),
        'before' => before,
        'after' => { 'root_entities' => model.entities.length, 'definition_entities' => definition.entities.length },
        'reference_name' => reference.name,
        'reference_pid' => reference.persistent_id,
        'model_path_before_save' => model.path,
        'sketchup_version' => Sketchup.version
      }
    end
  end
end
