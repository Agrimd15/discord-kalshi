
import asyncio
import json
import websockets
import discord
from auth import sign_request

WS_URL = "wss://api.elections.kalshi.com/trade-api/ws/v2"

async def start_stream(client: discord.Client, channel_id: int, key_id: str, private_key_path: str):
    """
    Connects to Kalshi WebSocket and streams 'fill' events to a Discord Channel.
    Designed to run as a background task.
    """
    print("Stream: Waiting for Discord Client...")
    await client.wait_until_ready()
    
    # 1. Resolve Channel (Robust Fetch)
    channel = None
    try:
        channel = await client.fetch_channel(channel_id)
        print(f"Stream: Linked to channel: {channel.name} ({channel.id})")
    except Exception as e:
        print(f"Stream Error: Could not find channel {channel_id}. Error: {e}")
        return

    print("Stream: Starting connection loop...")

    while not client.is_closed():
        try:
            # 2. Handshake (Sign Request)
            # Kalshi requires GET /trade-api/ws/v2 signature for connection
            path = "/trade-api/ws/v2"
            method = "GET"
            headers = sign_request(method, path, key_id, private_key_path)
            
            # 3. Connect
            async with websockets.connect(WS_URL, additional_headers=headers) as websocket:
                print("Stream: Connected to Kalshi WebSocket.")

                # 4. Subscribe
                subscribe_msg = {
                    "id": 1,
                    "cmd": "subscribe",
                    "params": {"channels": ["fill"]}
                }
                await websocket.send(json.dumps(subscribe_msg))
                print("Stream: Subscribed to 'fill' channel.")

                # 5. Listen Loop
                async for message_str in websocket:
                    try:
                        message = json.loads(message_str)
                        msg_type = message.get("type")
                        
                        if msg_type == "fill":
                            # Process Fill
                            # Payload structure varies, usually in 'msg' key
                            data = message.get("msg", message)
                            
                            ticker = data.get("ticker", "Unknown")
                            side = data.get("side", "Unknown").upper()
                            count = data.get("count", 0)
                            price = data.get("price", 0)
                            
                            # Format Price (Kalshi is cents)
                            price_display = f"{price}¢"
                            if price > 99: # Just in case it's dollars
                                price_display = f"${price/100:.2f}"

                            # Send Embed
                            embed = discord.Embed(
                                title="Order Filled",
                                description=f"**{side}** {count}x `{ticker}` @ {price_display}",
                                color=discord.Color.gold() # distinct from search
                            )
                            embed.set_footer(text="Real-time execution alert")
                            
                            await channel.send(embed=embed)
                        
                        elif msg_type == "error":
                            print(f"Stream WS Error: {message}")

                    except Exception as e:
                        print(f"Stream Message Error: {e}")

        except Exception as e:
            print(f"Stream Disconnected: {e}. Reconnecting in 5s...")
            await asyncio.sleep(5)
