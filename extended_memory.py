from langchain.memory import ConversationBufferMemory
from typing import Any, Dict, List


class ExtendedMemory(ConversationBufferMemory):
    extra_variables:List[str] = []

    @property
    def memory_variables(self) -> List[str]:
        """Will always return list of memory variables."""
        return [self.memory_key] + self.extra_variables

    def load_memory_variables(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Return buffer with history and extra variables"""
        d = super().load_memory_variables(inputs)
        d.update({k:inputs.get(k) for k in self.extra_variables})        
        return d