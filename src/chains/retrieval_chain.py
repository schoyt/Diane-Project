"""
retrieval_chain.py - Implements LangChain retrieval chain for querying transcript data
"""

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_chroma import Chroma
from langchain_core.documents import Document
from datetime import datetime, timedelta

class RetrievalChain:
    def __init__(self, vector_store, temperature=0.0):
        """
        Initialize the retrieval chain with a vector store
        
        Args:
            vector_store: Chroma instance
            temperature: Temperature for the LLM (lower = more deterministic)
        """
        self.vector_store = vector_store
        self.retriever = vector_store.as_retriever(search_kwargs={"k": 5})
        self.llm = ChatOpenAI(temperature=temperature)
        self.setup_chain()
        
    def setup_chain(self):
        """Set up the retrieval chain with appropriate prompts"""
        # Create the template for the system message
        template = """
        You are Diane, a personal memory assistant that helps users recall information 
        from their daily audio recordings. 
        
        Use the following pieces of retrieved context to answer the user's question.
        If you don't know the answer based on the provided context, say you don't know
        and suggest the user try a different query.
        
        Retrieved context:
        {context}
        
        User question: {question}
        """
        
        # Create the prompt
        prompt = ChatPromptTemplate.from_template(template)
        
        # Create the chain
        self.chain = (
            {"context": self.retriever, "question": RunnablePassthrough()}
            | prompt
            | self.llm
            | StrOutputParser()
        )
    
    def query(self, question):
        """
        Process a user query and return the response
        
        Args:
            question: User's natural language question
            
        Returns:
            str: Response to the user's query
        """
        try:
            return self.chain.invoke(question)
        except Exception as e:
            return f"Error processing query: {str(e)}"
            
    def add_documents(self, texts, metadatas=None):
        """
        Add documents to the vector store
        
        Args:
            texts: List of text content
            metadatas: List of metadata dictionaries
        """
        documents = []
        
        if metadatas:
            for i, (text, metadata) in enumerate(zip(texts, metadatas)):
                documents.append(Document(page_content=text, metadata=metadata))
        else:
            for i, text in enumerate(texts):
                documents.append(Document(page_content=text))
                
        # Add the documents to the vector store
        self.vector_store.add_documents(documents)