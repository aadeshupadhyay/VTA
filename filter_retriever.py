from typing import Any, Dict, List
from langchain.chains import ConversationalRetrievalChain
from langchain.callbacks.manager import CallbackManagerForChainRun
from langchain.docstore.document import Document
from langchain.vectorstores.base import VectorStoreRetriever
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
import os

class VectorStoreRetrieverWithFiltering(VectorStoreRetriever):
    '''Custom vectorstore retriever with filter functionality.'''
    
    def _get_relevant_documents(
        self,
        query: str,
        filter: Dict[str, Any] = None
    ) -> List[Document]:
        '''Override method with filter functionality.'''
        if self.search_type == "similarity" and filter:
            # Perform similarity search and apply filter if provided
            docs = self.vectorstore.similarity_search(query,k=200, **self.search_kwargs)
            if filter:
                # Apply filter manually if needed
                docs = [doc for doc in docs if doc.metadata.get('source') == filter['source']]
        elif self.search_type=="similarity":
            docs = self.vectorstore.similarity_search(query,k=5, **self.search_kwargs)

        else:
            raise NotImplementedError(f"Search type '{self.search_type}' not implemented.")
        
        return docs

class ConversationalRetrievalChainPassArgs(ConversationalRetrievalChain):
    '''Custom ConversationalRetrievalChain with filter functionality.'''
    
    def _get_docs(
        self,
        question: str,
        inputs: Dict[str, Any],
        *,
        run_manager: CallbackManagerForChainRun
    ) -> List[Document]:
        '''Override get docs with additional arguments.'''
        filter = inputs.get('filter', {})
        docs = self.retriever._get_relevant_documents(question, filter)
        return self._reduce_tokens_below_limit(docs)
