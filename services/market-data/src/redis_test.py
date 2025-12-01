import asyncio
import redis.asyncio as redis

async def main():
    r = redis.from_url("redis://localhost:6379/0")
    pong = await r.ping()
    print("PING:", pong)
asyncio.run(main())
