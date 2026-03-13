import asyncio
import sys

async def main():
    loop = asyncio.get_running_loop()
    print(f"Platform: {sys.platform}")
    print(f"Python: {sys.version}")
    print(f"Loop type: {type(loop)}")
    try:
        import playwright
        print("Playwright imported")
    except ImportError:
        print("Playwright NOT imported")

if __name__ == "__main__":
    asyncio.run(main())
