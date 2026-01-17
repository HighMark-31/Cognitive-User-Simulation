import asyncio
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.pool import NullPool
import os
from dotenv import load_dotenv

load_dotenv(override=True)

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    discord_id = Column(String(50), unique=True, nullable=False)
    username = Column(String(100), nullable=False)
    display_name = Column(String(100))
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)
    server_id = Column(String(50), nullable=True)
    server_name = Column(String(200), nullable=True)
    is_suspicious = Column(Boolean, default=False)
    suspicion_count = Column(Integer, default=0)
    
    messages = relationship("Message", back_populates="user", cascade="all, delete-orphan")
    interactions = relationship("Interaction", back_populates="user", cascade="all, delete-orphan")

class Message(Base):
    __tablename__ = 'messages'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    discord_message_id = Column(String(50), unique=True, nullable=False)
    channel_id = Column(String(50), nullable=False)
    channel_name = Column(String(100))
    server_id = Column(String(50), nullable=True)
    server_name = Column(String(200), nullable=True)
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    is_dm = Column(Boolean, default=False)
    
    user = relationship("User", back_populates="messages")

class BotResponse(Base):
    __tablename__ = 'bot_responses'
    
    id = Column(Integer, primary_key=True)
    discord_message_id = Column(String(50), unique=True, nullable=False)
    channel_id = Column(String(50), nullable=False)
    server_id = Column(String(50), nullable=True)
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    action_type = Column(String(50))
    is_dm = Column(Boolean, default=False)
    planned_by_ai = Column(Boolean, default=True)

class Interaction(Base):
    __tablename__ = 'interactions'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    interaction_type = Column(String(50), nullable=False)
    content = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    channel_id = Column(String(50))
    server_id = Column(String(50))
    
    user = relationship("User", back_populates="interactions")

class SocialTestLog(Base):
    __tablename__ = 'social_test_logs'
    
    id = Column(Integer, primary_key=True)
    log_type = Column(String(50), nullable=False)
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    server_id = Column(String(50), nullable=True)
    server_name = Column(String(200), nullable=True)
    channel_id = Column(String(50), nullable=True)

class DatabaseManager:
    def __init__(self):
        database_url = os.getenv('DATABASE_URL', 'sqlite+aiosqlite:///discord_bot.db')
        self.engine = create_async_engine(
            database_url,
            echo=False,
            poolclass=NullPool
        )
        self.async_session = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
    
    async def initialize(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    
    async def close(self):
        await self.engine.dispose()
    
    async def get_or_create_user(self, discord_id, username, display_name=None, server_id=None, server_name=None):
        async with self.async_session() as session:
            from sqlalchemy import select
            from sqlalchemy.exc import IntegrityError
            
            result = await session.execute(
                select(User).where(User.discord_id == str(discord_id))
            )
            user = result.scalar_one_or_none()
            
            if not user:
                user = User(
                    discord_id=str(discord_id),
                    username=username,
                    display_name=display_name or username,
                    server_id=str(server_id) if server_id else None,
                    server_name=server_name
                )
                session.add(user)
                try:
                    await session.commit()
                    await session.refresh(user)
                except IntegrityError:
                    await session.rollback()
                    # Se fallisce per UNIQUE constraint, riprova a prenderlo
                    result = await session.execute(
                        select(User).where(User.discord_id == str(discord_id))
                    )
                    user = result.scalar_one_or_none()
            else:
                user.last_seen = datetime.utcnow()
                user.username = username
                user.display_name = display_name or username
                if server_id:
                    user.server_id = str(server_id)
                if server_name:
                    user.server_name = server_name
                try:
                    await session.commit()
                except IntegrityError:
                    await session.rollback()
            
            return user
    
    async def save_message(self, discord_id, username, display_name, discord_message_id, channel_id, 
                          channel_name, content, server_id=None, server_name=None, is_dm=False):
        user = await self.get_or_create_user(discord_id, username, display_name, server_id, server_name)
        
        async with self.async_session() as session:
            from sqlalchemy import select
            from sqlalchemy.exc import IntegrityError
            
            result = await session.execute(
                select(Message).where(Message.discord_message_id == str(discord_message_id))
            )
            existing = result.scalar_one_or_none()
            
            if not existing:
                message = Message(
                    user_id=user.id,
                    discord_message_id=str(discord_message_id),
                    channel_id=str(channel_id),
                    channel_name=channel_name,
                    server_id=str(server_id) if server_id else None,
                    server_name=server_name,
                    content=content,
                    is_dm=is_dm
                )
                session.add(message)
                try:
                    await session.commit()
                    return message
                except IntegrityError:
                    await session.rollback()
                    # Se fallisce, probabilmente un'altra task lo ha già inserito
                    result = await session.execute(
                        select(Message).where(Message.discord_message_id == str(discord_message_id))
                    )
                    return result.scalar_one_or_none()
            return existing
    
    async def save_bot_response(self, discord_message_id, channel_id, content, action_type, 
                              server_id=None, is_dm=False, planned_by_ai=True):
        async with self.async_session() as session:
            from sqlalchemy import select
            from sqlalchemy.exc import IntegrityError
            
            result = await session.execute(
                select(BotResponse).where(BotResponse.discord_message_id == str(discord_message_id))
            )
            existing = result.scalar_one_or_none()
            
            if not existing:
                response = BotResponse(
                    discord_message_id=str(discord_message_id),
                    channel_id=str(channel_id),
                    server_id=str(server_id) if server_id else None,
                    content=content,
                    action_type=action_type,
                    is_dm=is_dm,
                    planned_by_ai=planned_by_ai
                )
                session.add(response)
                try:
                    await session.commit()
                    return response
                except IntegrityError:
                    await session.rollback()
                    result = await session.execute(
                        select(BotResponse).where(BotResponse.discord_message_id == str(discord_message_id))
                    )
                    return result.scalar_one_or_none()
            return existing
    
    async def save_interaction(self, user_id, interaction_type, content=None, channel_id=None, server_id=None):
        async with self.async_session() as session:
            interaction = Interaction(
                user_id=user_id,
                interaction_type=interaction_type,
                content=content,
                channel_id=str(channel_id) if channel_id else None,
                server_id=str(server_id) if server_id else None
            )
            session.add(interaction)
            await session.commit()
            return interaction
    
    async def log_suspicion(self, discord_id, username, reason):
        async with self.async_session() as session:
            from sqlalchemy import select
            result = await session.execute(
                select(User).where(User.discord_id == str(discord_id))
            )
            user = result.scalar_one_or_none()
            
            if user:
                user.suspicion_count += 1
                user.is_suspicious = True
                await session.commit()
            
            await self.save_log('SUSPICION', f'User {username} ({discord_id}) - {reason}')
    
    async def save_log(self, log_type, content, server_id=None, server_name=None, channel_id=None):
        async with self.async_session() as session:
            log = SocialTestLog(
                log_type=log_type,
                content=content,
                server_id=str(server_id) if server_id else None,
                server_name=server_name,
                channel_id=str(channel_id) if channel_id else None
            )
            session.add(log)
            await session.commit()
            return log
    
    async def get_user_stats(self):
        async with self.async_session() as session:
            from sqlalchemy import select, func
            result = await session.execute(
                select(
                    func.count(User.id).label('total_users'),
                    func.count(User.id).filter(User.is_suspicious == True).label('suspicious_users'),
                    func.sum(User.suspicion_count).label('total_suspicions')
                )
            )
            return result.one()
    
    async def get_message_stats(self):
        async with self.async_session() as session:
            from sqlalchemy import select, func
            total_messages = await session.scalar(select(func.count(Message.id)))
            dm_messages = await session.scalar(select(func.count(Message.id)).where(Message.is_dm == True))
            bot_responses = await session.scalar(select(func.count(BotResponse.id)))
            return (total_messages, dm_messages, bot_responses)

db_manager = DatabaseManager()
