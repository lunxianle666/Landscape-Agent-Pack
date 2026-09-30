# Acceptance-only traversal, independent of the already accepted Bridge core.
require 'json'
module LAPProductionTypes
  module_function
  def walk(entities, counts, depth=0)
    raise 'Nesting limit' if depth>16
    entities.each do |e|
      counts[e.typename]+=1
      if e.is_a?(Sketchup::ComponentInstance)
        walk(e.definition.entities,counts,depth+1)
      elsif e.is_a?(Sketchup::Group)
        walk(e.entities,counts,depth+1)
      end
    end
  end
  def write(path)
    raise 'Existing type report' if File.exist?(path)
    counts=Hash.new(0)
    walk(Sketchup.active_model.entities,counts)
    File.open(path,'wx'){|f| f.write(JSON.pretty_generate(counts))}
    counts
  end
end
