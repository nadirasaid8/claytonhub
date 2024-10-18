import sys
import asyncio
from src import *
from src.deeplchain import _banner, _clear

if __name__ == "__main__":
    _clear()
    _banner()
    while True:
        try:
            asyncio.run(main())
        except KeyboardInterrupt:
            log(mrh + f"Stopping due to keyboard interrupt.")
            sys.exit()
