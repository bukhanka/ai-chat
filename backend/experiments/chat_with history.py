import os
from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnablePassthrough, RunnableConfig
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.chat_history import BaseChatMemory
from langchain.memory import ConversationBufferMemory

class ContractAdvisorChat:
    def __init__(self, api_key: str):
        """
        Initialize the Conversational Contract Advisor
        
        Args:
            api_key (str): OpenAI API key for authentication
        """
        # Initialize the language model
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            api_key=api_key,
            temperature=0.7  # Balanced creativity and precision
        )
        
        # Initialize conversation memory
        self.memory = ConversationBufferMemory(
            return_messages=True, 
            human_prefix="User", 
            ai_prefix="Assistant"
        )
        
        # Define the initial system prompt
        self.system_prompt = SystemMessage(content="""
        You are an AI Contract Advisor Assistant. Your goal is to help users find the most appropriate contract template 
        by asking clarifying questions and understanding their specific needs. 
        
        Conversation Flow:
        1. Listen carefully to the user's initial description
        2. Ask targeted clarifying questions to understand:
           - Nature of the project/relationship
           - Parties involved
           - Specific requirements and expectations
           - Potential risks or special considerations
        3. Once you have sufficient information, recommend a specific contract template
        4. Provide detailed insights about the recommended template
        
        Communication Style:
        - Be professional and precise
        - Ask one question at a time
        - Guide the conversation systematically
        - Demonstrate deep understanding of legal and contractual nuances
        """)
        
        # Create the conversational chain
        self.prompt = ChatPromptTemplate.from_messages([
            self.system_prompt,
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{user_input}")
        ])
        
        self.chain = (
            RunnablePassthrough.assign(
                chat_history=lambda x: self.memory.chat_memory.messages
            )
            | self.prompt
            | self.llm
            | StrOutputParser()
        )
    
    def process_conversation(self, user_input: str) -> Dict[str, Any]:
        """
        Process user input and generate appropriate response
        
        Args:
            user_input (str): User's message
        
        Returns:
            Dict with conversation response and state
        """
        try:
            # Add user input to memory
            self.memory.chat_memory.add_user_message(user_input)
            
            # Generate response
            response = self.chain.invoke({
                "user_input": user_input
            })
            
            # Add AI response to memory
            self.memory.chat_memory.add_ai_message(response)
            
            # Determine if we're ready to recommend a contract
            is_ready_for_recommendation = self._check_recommendation_readiness()
            
            return {
                "success": True,
                "response": response,
                "ready_for_recommendation": is_ready_for_recommendation
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _check_recommendation_readiness(self) -> bool:
        """
        Determine if enough information has been gathered to recommend a contract
        
        Returns:
            bool: Whether a contract recommendation can be made
        """
        # Implement logic to check conversation completeness
        # This could involve checking:
        # 1. Number of exchanges
        # 2. Presence of key information
        # 3. Explicit confirmation from the AI
        
        messages = self.memory.chat_memory.messages
        
        # Example simple check
        if len(messages) > 5:  # At least 5 message exchanges
            last_ai_message = messages[-1]
            if "I believe I now have enough information" in last_ai_message.content:
                return True
        
        return False
    
    def get_contract_recommendation(self) -> Dict[str, Any]:
        """
        Generate final contract recommendation based on conversation history
        
        Returns:
            Dict with contract recommendation details
        """
        try:
            # Compile conversation history
            conversation_context = "\n".join([
                f"{msg.type}: {msg.content}" 
                for msg in self.memory.chat_memory.messages
            ])
            
            # Create a specialized prompt for recommendation
            recommendation_prompt = ChatPromptTemplate.from_messages([
                SystemMessage(content="""
                Based on the entire conversation, provide a comprehensive contract recommendation.
                Include:
                1. Recommended Contract Template
                2. Key Considerations
                3. Potential Risks
                4. Suggested Modifications
                """),
                ("human", "{conversation_context}")
            ])
            
            recommendation_chain = (
                recommendation_prompt 
                | self.llm 
                | StrOutputParser()
            )
            
            recommendation = recommendation_chain.invoke({
                "conversation_context": conversation_context
            })
            
            return {
                "success": True,
                "recommendation": self._parse_recommendation(recommendation)
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _parse_recommendation(self, response: str) -> Dict[str, Any]:
        """
        Parse the recommendation response into a structured format
        
        Args:
            response (str): Raw recommendation text
        
        Returns:
            Parsed recommendation dictionary
        """
        sections = response.split('\n\n')
        parsed = {}
        
        for section in sections:
            if ':' in section:
                key, value = section.split(':', 1)
                parsed[key.strip()] = value.strip()
        
        return parsed

# Example usage function
def contract_advisor_chat(api_key: str, messages: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    Manage contract advisor chat session
    
    Args:
        api_key (str): OpenAI API key
        messages (List[Dict]): Conversation history
    
    Returns:
        Dict with conversation response
    """
    advisor = ContractAdvisorChat(api_key)
    
    # Process existing conversation history
    for msg in messages:
        result = advisor.process_conversation(msg['content'])
        
        # Check if recommendation is ready
        if result.get('ready_for_recommendation', False):
            return advisor.get_contract_recommendation()
    
    # Return latest conversation response
    return result

# Only run if script is executed directly
if __name__ == "__main__":
    api_key = os.getenv("OPENAI_API_KEY")
    
    # Simulate conversation
    conversation = [
        {"role": "user", "content": "I want to start a software development project"},
        {"role": "user", "content": "It's a web application for managing customer relationships"}
    ]
    
    recommendation = contract_advisor_chat(api_key, conversation)
    print(recommendation)