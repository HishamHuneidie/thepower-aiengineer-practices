from typing import List
from dotenv import load_dotenv
import os

from fastapi import APIRouter, Depends, HTTPException, Response, status
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI


from app.contexts.messages.application.dtos import MessageCreate, MessageRead
from app.contexts.messages.application.use_cases import (
    CreateMessage,
    DeleteMessage,
    GetMessage,
    ListMessages,
)
from app.contexts.messages.infrastructure.repository import (
    SqlRelationError,
    MessageRepository,
)

load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

router = APIRouter(prefix="/messages", tags=["messages"])


def get_message_repository():
    return MessageRepository()


@router.get("", response_model=List[MessageRead])
def list_messages(repository=Depends(get_message_repository)):
    return ListMessages(repository).execute()


@router.post("", response_model=MessageRead, status_code=status.HTTP_201_CREATED)
def create_Message(payload: MessageCreate, repository=Depends(get_message_repository)):
    try:
        """
            api key
            
            prompt template
            model
            parser
            
            cadena
            
            invoke answer
        """
        
        template_messages = [
            ('system', 'Eres un historiador de primera y siempre respondes extremadamente conciso y breve'),
            ('human', '{question}'),
        ]
        
        prompt = ChatPromptTemplate.from_messages(template_messages)
        model = ChatOpenAI(model='gpt-3.5-turbo', temperature=0)
        parser = StrOutputParser()
        
        chain = prompt | model | parser
        
        new_message = payload.model_dump();
        
        new_message['answer'] = chain.invoke({"question": new_message['question']})
        
        return CreateMessage(repository).execute(new_message)
    except SqlRelationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("/{message_id}", response_model=MessageRead)
def get_message(message_id: int, repository=Depends(get_message_repository)):
    message = GetMessage(repository).execute(message_id)
    if message is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")
    return message


@router.delete("/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_message(message_id: int, repository=Depends(get_message_repository)):
    deleted = DeleteMessage(repository).execute(message_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
