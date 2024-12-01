import os
from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

class ContractGenerator:
    def __init__(self, api_key: str):
        """
        Initialize the contract generation tool
        
        Args:
            api_key (str): OpenAI API key
        """
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            api_key=api_key,
            temperature=0.6  # Balance creativity and precision
        )
    
    def generate_contract(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a contract based on user context
        
        Args:
            context (Dict): Context for contract generation
        
        Returns:
            Dict with generated contract
        """
        generation_prompt = ChatPromptTemplate.from_messages([
            ("system", """
            Generate a legal contract based on the provided context.
            Follow Russian legal standards and ensure comprehensive coverage.
            
            Contract Generation Steps:
            1. Identify contract type
            2. Create dynamic input fields
            3. Generate contract template
            4. Provide explanations for key sections
            """),
            ("human", """
            Generate a contract with these details:
            Contract Type: {contract_type}
            Parties: {parties}
            Key Terms: {key_terms}
            Additional Context: {additional_context}
            """)
        ])
        
        chain = generation_prompt | self.llm | StrOutputParser()
        
        try:
            contract_text = chain.invoke({
                "contract_type": context.get('contract_type', 'Undefined'),
                "parties": context.get('parties', 'Not Specified'),
                "key_terms": context.get('key_terms', 'No specific terms'),
                "additional_context": context.get('additional_context', '')
            })
            
            return {
                "success": True,
                "contract": self._parse_contract(contract_text),
                "input_fields": self._generate_input_fields(context)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _parse_contract(self, contract_text: str) -> Dict[str, str]:
        """
        Parse contract into structured sections
        """
        sections = {}
        current_section = None
        
        for line in contract_text.split('\n'):
            if ':' in line:
                current_section, content = line.split(':', 1)
                sections[current_section.strip()] = content.strip()
            elif current_section:
                sections[current_section] += ' ' + line.strip()
        
        return sections
    
    def _generate_input_fields(self, context: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Generate dynamic input fields based on contract context
        """
        input_fields = [
            {"name": "party1_name", "label": "Название первой стороны", "type": "text"},
            {"name": "party2_name", "label": "Название второй стороны", "type": "text"}
        ]
        
        # Add context-specific fields
        if context.get('contract_type') == 'service':
            input_fields.extend([
                {"name": "service_description", "label": "Описание услуги", "type": "textarea"},
                {"name": "service_price", "label": "Стоимость услуги", "type": "number"}
            ])
        
        return input_fields

def generate_contract_from_context(api_key: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Wrapper function for contract generation
    
    Args:
        api_key (str): OpenAI API key
        context (Dict): Context for contract generation
    
    Returns:
        Generated contract
    """
    generator = ContractGenerator(api_key)
    return generator.generate_contract(context)

# Example usage when script is run directly
if __name__ == "__main__":
    api_key = os.getenv("OPENAI_API_KEY")
    sample_context = {
        "contract_type": "service",
        "parties": ["ООО Технология", "ИП Иванов"],
        "key_terms": "Разработка веб-приложения"
    }
    
    result = generate_contract_from_context(api_key, sample_context)
    print(result) 