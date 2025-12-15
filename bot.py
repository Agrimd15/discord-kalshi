
import os
import discord
from discord.ext import commands, tasks
import aiohttp
import websockets
import json
import asyncio
from dotenv import load_dotenv

# Import our helper function
from auth import sign_request

# Load environment variables
load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
DISCORD_CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID"))
KALSHI_KEY_ID = os.getenv("KALSHI_KEY_ID")
KALSHI_PRIVATE_KEY_PATH = os.getenv("KALSHI_PRIVATE_KEY_PATH")

# REST API Base URL
BASE_URL = "https://api.elections.kalshi.com"

# WebSocket URL
WS_URL = "wss://api.elections.kalshi.com/trade-api/ws/v2"

# Bot Setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    # Start the WebSocket background task
    bot.loop.create_task(order_fill_listener())

@bot.command(aliases=['bal'])
async def balance(ctx):
    """
    Fetches the user's current cash balance on Kalshi.
    Endpoint: GET /trade-api/v2/portfolio/balance
    """
    path = "/trade-api/v2/portfolio/balance"
    method = "GET"
    
    # 1. Generate Headers
    try:
        headers = sign_request(method, path, KALSHI_KEY_ID, KALSHI_PRIVATE_KEY_PATH)
    except Exception as e:
        await ctx.send(f"Error signing request: {e}")
        return

    # 2. Make the Request
    url = f"{BASE_URL}{path}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                # Assuming the response structure is like { "balance": 125000 } in cents
                # Adjust based on exact API response structure if needed. 
                # Documentation usually says balance is integer cents.
                
                # Careful: The response might be nested under 'balance' key or similar if it returns a wrapper object.
                # Let's assume standard Kalshi v2 response format: {"balance": 10000}
                
                cents = data.get("balance", 0)
                dollars = cents / 100
                formatted_balance = f"${dollars:,.2f}"
                await ctx.send(f"Current Balance: **{formatted_balance}**")
            else:
                error_text = await response.text()
                await ctx.send(f"Failed to fetch balance. Status: {response.status}\nError: {error_text}")

async def order_fill_listener():
    """
    Background task to listen for 'fill' messages on Kalshi WebSocket.
    """
    await bot.wait_until_ready()
    channel = bot.get_channel(DISCORD_CHANNEL_ID)
    
    if not channel:
        print(f"Error: Channel with ID {DISCORD_CHANNEL_ID} not found.")
        return

    print("Starting WebSocket Listener...")

    while not bot.is_closed():
        try:
            # 1. Sign the connection request (Handshake)
            path = "/trade-api/ws/v2"
            method = "GET"
            headers = sign_request(method, path, KALSHI_KEY_ID, KALSHI_PRIVATE_KEY_PATH)
            
            # Note: websockets library expects headers as a dict or list of tuples.
            # Our sign_request returns a dict, which is compatible.

            async with websockets.connect(WS_URL, additional_headers=headers) as websocket:
                print("Connected to Kalshi WebSocket.")

                # 2. Subscribe to 'fill' channel
                subscribe_msg = {
                    "id": 1,
                    "cmd": "subscribe",
                    "params": {
                        "channels": ["fill"]
                    }
                }
                await websocket.send(json.dumps(subscribe_msg))
                print("Subscribed to fills.")

                # 3. Listen for messages
                async for message_str in websocket:
                    try:
                        message = json.loads(message_str)
                        
                        # Check message type
                        msg_type = message.get("type")
                        
                        if msg_type == "fill":
                            # Extract details
                            # Example payload structure from docs/experience:
                            # {"type": "fill", "msg": { "ticker": "NBX", "is_taker": true, "side": "yes", "count": 10, "price": 50, ... } }
                            # Adjust based on actual message structure.
                            
                            # Usually the data is inside 'msg' or top level depending on version.
                            # Let's inspect 'msg' if present, else use top level.
                            data = message.get("msg", message)
                            
                            ticker = data.get("ticker", "Unknown")
                            side = data.get("side", "Unknown").upper() # buy/sell or yes/no
                            action = data.get("action", side) # Sometimes 'action' is 'buy'/'sell'
                            price = data.get("price", 0) / 100 # Assuming price is in cents? Often Kalshi uses probability 1-99 or cents. 
                            # Actually price on Kalshi is typically 1-99 cents for Yes/No contracts. 
                            # If it's pure 1-99, we might not divide by 100 if we want to show '50c'.
                            # But usually formatted as $0.50 is safer or 50¢. Let's assume cents integer.
                            
                            count = data.get("count", 0)

                            # different format for price display maybe?
                            price_display = f"{data.get('price', 0)}¢"

                            embed = discord.Embed(
                                title="🚨 Order Filled!",
                                color=discord.Color.green()
                            )
                            embed.add_field(name="Ticker", value=ticker, inline=True)
                            embed.add_field(name="Action", value=action, inline=True)
                            embed.add_field(name="Price", value=price_display, inline=True)
                            embed.add_field(name="Count", value=str(count), inline=True)
                            
                            await channel.send(embed=embed)
                        
                        elif msg_type == "error":
                            print(f"WS Error: {message}")

                    except json.JSONDecodeError:
                        print(f"Failed to decode JSON: {message_str}")
                    except Exception as e:
                        print(f"Error processing message: {e}")

        except Exception as e:
            print(f"WebSocket connection lost: {e}. Reconnecting in 5 seconds...")
            await asyncio.sleep(5)

if __name__ == "__main__":
    if not DISCORD_TOKEN:
        print("Error: DISCORD_TOKEN not found in .env")
    else:
        bot.run(DISCORD_TOKEN)
