"""Data models package"""

from .customer import Customer, CustomerCreate, CustomerUpdate, CustomerProfile, CustomerIdentifier
from .conversation import Conversation, ConversationCreate, ConversationUpdate
from .message import Message, MessageCreate
from .ticket import Ticket, TicketCreate, TicketUpdate, TicketSummary
from .knowledge_base import (
    KnowledgeBaseEntry,
    KnowledgeBaseEntryCreate,
    KnowledgeBaseEntryWithScore,
    KnowledgeBaseSearchResult
)

__all__ = [
    'Customer',
    'CustomerCreate',
    'CustomerUpdate',
    'CustomerProfile',
    'CustomerIdentifier',
    'Conversation',
    'ConversationCreate',
    'ConversationUpdate',
    'Message',
    'MessageCreate',
    'Ticket',
    'TicketCreate',
    'TicketUpdate',
    'TicketSummary',
    'KnowledgeBaseEntry',
    'KnowledgeBaseEntryCreate',
    'KnowledgeBaseEntryWithScore',
    'KnowledgeBaseSearchResult'
]
