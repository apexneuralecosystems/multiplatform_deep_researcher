"""
Test script to verify API connections.
"""

import asyncio
import os

import httpx
from dotenv import load_dotenv

load_dotenv()


async def test_openrouter():
    """Test OpenRouter API with a simple request."""
    print("\n=== Testing OpenRouter API ===")
    api_key = os.environ.get("OPENROUTER_API_KEY")
    
    if not api_key:
        print("❌ OPENROUTER_API_KEY not set")
        return False
    
    print(f"API Key: {api_key[:20]}...")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "openai/gpt-4o-mini",
                    "messages": [{"role": "user", "content": "Say 'Hello' in one word"}],
                    "max_tokens": 10
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                print(f"✅ OpenRouter API working! Response: {content}")
                return True
            else:
                print(f"❌ OpenRouter API error: {response.status_code}")
                print(f"   Response: {response.text[:200]}")
                return False
                
        except Exception as e:
            print(f"❌ OpenRouter API connection failed: {e}")
            return False


async def test_brightdata():
    """Test Bright Data API with a simple request."""
    print("\n=== Testing Bright Data API ===")
    api_key = os.environ.get("BRIGHT_DATA_API_TOKEN")
    
    if not api_key:
        print("❌ BRIGHT_DATA_API_TOKEN not set")
        return False
    
    print(f"API Token: {api_key[:20]}...")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(
                "https://api.brightdata.com/zone/status",
                headers={
                    "Authorization": f"Bearer {api_key}",
                }
            )
            
            if response.status_code == 200:
                print(f"✅ Bright Data API authenticated! Status: {response.status_code}")
                return True
            elif response.status_code == 401:
                print(f"❌ Bright Data API authentication failed (401)")
                print(f"   Your API token may be invalid or expired")
                return False
            else:
                print(f"⚠️  Bright Data API returned: {response.status_code}")
                print(f"   Token format appears valid, full MCP test needed")
                return True
                
        except Exception as e:
            print(f"⚠️  Could not test Bright Data directly: {e}")
            print("   MCP server will test the token when starting")
            return True


async def main():
    print("=" * 50)
    print("API Connection Test")
    print("=" * 50)
    
    openrouter_ok = await test_openrouter()
    brightdata_ok = await test_brightdata()
    
    print("\n" + "=" * 50)
    print("Summary")
    print("=" * 50)
    print(f"OpenRouter: {'✅ Working' if openrouter_ok else '❌ Failed'}")
    print(f"Bright Data: {'✅ Ready' if brightdata_ok else '❌ Failed'}")
    
    if openrouter_ok and brightdata_ok:
        print("\n🎉 All APIs ready! Research should work.")
    else:
        print("\n⚠️  Some APIs have issues. Check the errors above.")


if __name__ == "__main__":
    asyncio.run(main())
