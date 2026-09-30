# Save and switch models only outside an open SketchUp operation.
module LandscapeAgentPack
  module Persistence
    module_function

    def save(startup, output)
      model = Sketchup.active_model
      raise 'Wrong startup model' unless NativeImport.normalized(model.path) == NativeImport.normalized(startup)
      raise 'Output exists' if File.exist?(output)
      raise 'Output directory missing' unless Dir.exist?(File.dirname(output))
      raise 'Save failed' unless model.save(output) && File.size(output) > 0
      raise 'Save path mismatch' unless NativeImport.normalized(model.path) == NativeImport.normalized(output)
      {'path' => model.path, 'bytes' => File.size(output), 'modified' => model.modified?}
    end

    def close_saved(output)
      model = Sketchup.active_model
      raise 'Wrong saved model' unless NativeImport.normalized(model.path) == NativeImport.normalized(output)
      raise 'Unsaved model changes' if model.modified?
      Sketchup.file_new
      # SketchUp 2023 reuses its Ruby Model wrapper on File > New. Object ID
      # and Ringo model_id therefore do not prove replacement.
      replacement = Sketchup.active_model
      raise 'Model path was not cleared' unless replacement.path.empty?
      raise 'CAD reference survived File New' if replacement.entities.any? { |e| e.respond_to?(:name) && e.name == 'CAD_REFERENCE' }
      {'closed_path' => output, 'replacement_path' => Sketchup.active_model.path,
       'model_replaced' => true}
    end

    def reopen(output)
      raise 'Replacement model is dirty' if Sketchup.active_model.modified?
      raise 'SKP missing' unless File.file?(output)
      status = Sketchup.open_file(output, :with_status => true)
      raise 'Reopen failed' unless status == Sketchup::Model::LOAD_STATUS_SUCCESS
      raise 'Reopened path mismatch' unless NativeImport.normalized(Sketchup.active_model.path) == NativeImport.normalized(output)
      {'load_status' => status, 'path' => Sketchup.active_model.path}
    end
  end
end
