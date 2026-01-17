import asyncio
from datetime import datetime, timedelta
from database import db_manager
from sqlalchemy import select, func, desc
from database import User, Message, BotResponse, SocialTestLog

async def show_stats():
    print("\n" + "="*60)
    print("DISCORD AI BOT STATS")
    print("="*60 + "\n")
    
    user_stats = await db_manager.get_user_stats()
    message_stats = await db_manager.get_message_stats()
    
    print("GENERAL STATS")
    print("-" * 40)
    print(f"Total users: {user_stats[0]}")
    print(f"Suspicious users: {user_stats[1]}")
    print(f"Total suspicions: {user_stats[2]}")
    print(f"Messages received: {message_stats[0]}")
    print(f"DM messages: {message_stats[1]}")
    print(f"Bot responses: {message_stats[2]}")
    
    print("\nRECENT ACTIVITY (LAST 24H)")
    print("-" * 40)
    
    async with db_manager.async_session() as session:
        yesterday = datetime.now() - timedelta(hours=24)
        
        result = await session.execute(
            select(func.count(Message.id)).where(Message.timestamp >= yesterday)
        )
        recent_messages = result.scalar()
        
        result = await session.execute(
            select(func.count(BotResponse.id)).where(BotResponse.timestamp >= yesterday)
        )
        recent_responses = result.scalar()
        
        print(f"Messages received: {recent_messages}")
        print(f"Responses sent: {recent_responses}")
    
    print("\nTOP 5 USERS BY INTERACTIONS")
    print("-" * 40)
    
    async with db_manager.async_session() as session:
        result = await session.execute(
            select(
                User.username,
                User.server_name,
                func.count(Message.id).label('msg_count')
            )
            .join(Message, User.id == Message.user_id)
            .group_by(User.id)
            .order_by(desc('msg_count'))
            .limit(5)
        )
        
        for row in result:
            print(f"{row.username} - {row.msg_count} messages ({row.server_name})")
    
    print("\nLATEST 10 SUSPICIONS")
    print("-" * 40)
    
    async with db_manager.async_session() as session:
        result = await session.execute(
            select(SocialTestLog)
            .where(SocialTestLog.log_type == 'SUSPICION')
            .order_by(desc(SocialTestLog.timestamp))
            .limit(10)
        )
        
        for log in result.scalars():
            print(f"[{log.timestamp.strftime('%Y-%m-%d %H:%M')}] {log.content}")
    
    print("\nLATEST 10 LOGS")
    print("-" * 40)
    
    async with db_manager.async_session() as session:
        result = await session.execute(
            select(SocialTestLog)
            .order_by(desc(SocialTestLog.timestamp))
            .limit(10)
        )
        
        for log in result.scalars():
            print(f"[{log.timestamp.strftime('%Y-%m-%d %H:%M')}] {log.log_type}: {log.content[:80]}...")
    
    print("\n" + "="*60 + "\n")

async def export_data(filename="discord_bot_export.txt"):
    print(f"\nExporting data to {filename}...")
    
    async with db_manager.async_session() as session:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("="*60 + "\n")
            f.write("DISCORD AI BOT DATA EXPORT\n")
            f.write(f"Exported at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("="*60 + "\n\n")
            
            f.write("USERS\n")
            f.write("-" * 40 + "\n")
            result = await session.execute(select(User))
            for user in result.scalars():
                f.write(f"ID: {user.discord_id} | Username: {user.username} | ")
                f.write(f"Server: {user.server_name} | Suspicious: {user.is_suspicious} | ")
                f.write(f"Suspicion count: {user.suspicion_count}\n")
            
            f.write("\nRECEIVED MESSAGES\n")
            f.write("-" * 40 + "\n")
            result = await session.execute(select(Message).limit(50))
            for msg in result.scalars():
                f.write(f"[{msg.timestamp.strftime('%Y-%m-%d %H:%M')}] ")
                f.write(f"#{msg.channel_name} | {msg.content[:100]}...\n")
            
            f.write("\nBOT RESPONSES\n")
            f.write("-" * 40 + "\n")
            result = await session.execute(select(BotResponse).limit(50))
            for resp in result.scalars():
                f.write(f"[{resp.timestamp.strftime('%Y-%m-%d %H:%M')}] ")
                f.write(f"Type: {resp.action_type} | {resp.content[:100]}...\n")
            
            f.write("\nSUSPICION LOGS\n")
            f.write("-" * 40 + "\n")
            result = await session.execute(
                select(SocialTestLog)
                .where(SocialTestLog.log_type == 'SUSPICION')
            )
            for log in result.scalars():
                f.write(f"[{log.timestamp.strftime('%Y-%m-%d %H:%M')}] {log.content}\n")
    
    print(f"Export completed")

async def main():
    await db_manager.initialize()
    
    while True:
        print("\nDISCORD AI BOT STATS VIEWER")
        print("="*50)
        print("1. Show general stats")
        print("2. Export data to file")
        print("3. Exit")
        print("="*50)
        
        choice = input("\nChoose an option (1-3): ").strip()
        
        if choice == '1':
            await show_stats()
        elif choice == '2':
            filename = input("File name (press Enter for default): ").strip()
            if not filename:
                filename = "discord_bot_export.txt"
            await export_data(filename)
        elif choice == '3':
            print("Goodbye!")
            break
        else:
            print("Invalid option!")
    
    await db_manager.close()

if __name__ == '__main__':
    asyncio.run(main())
