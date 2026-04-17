class World:

    def __init__(self):
        self._next_entity_id = 0
        self._components = {}  
        self._processors = []

    def create_entity(self):
        
        self._next_entity_id += 1
        return self._next_entity_id

    def add_component(self, entity, component):
       
        comp_type = type(component)
        if comp_type not in self._components:
            self._components[comp_type] = {}
        self._components[comp_type][entity] = component

    def component_for_entity(self, entity, comp_type):
     
        return self._components.get(comp_type, {}).get(entity)

    def has_component(self, entity, comp_type):
        
        return entity in self._components.get(comp_type, {})

    def get_components(self, *types):
        if not types: return

        for t in types:
            if t not in self._components or not self._components[t]:
                return
                
        rarest_type = min(types, key=lambda t: len(self._components[t]))
        dicts_alvo = [self._components[t] for t in types]

        for ent in list(self._components[rarest_type].keys()):
            comps = []
            has_all = True
            
            for comp_dict in dicts_alvo:
                comp = comp_dict.get(ent)
                if comp is not None:
                    comps.append(comp)
                else:
                    has_all = False
                    break 
            
            if has_all:
                yield ent, comps

    def delete_entity(self, entity):
     
        for comp_map in self._components.values():
            comp_map.pop(entity, None)

    def add_processor(self, processor):

        processor.world = self
        self._processors.append(processor)

    def process(self, *args):
      
        for processor in self._processors:
            processor.process(*args)

class Processor:
    
    def __init__(self):
        self.world = None
        
    def process(self, *args):
        pass
