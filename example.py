"""Run an example script to quickly test."""
import asyncio

from aiohttp import ClientSession

from simplipy import Client
from simplipy.errors import SimplipyError
from simplipy.system import SystemStates


async def client_ss3(websession: ClientSession) -> None:
    """Test a v3 SimpliSafe client."""
    client = Client('bachya1208@gmail.com', websession)
    await client.authenticate_password("VNm'e^0vacDuke8jTie7")

    print('USER ID:')
    print(client.user_id)
    print()

    print('NUMBER OF SYSTEMS:')
    print(len(client.systems))
    print()

    print('FIRST SYSTEM: PROPERTIES')
    system = client.systems[0]
    print(system.__dict__)
    print()

    print('FIRST SYSTEM: NUMBER OF EVENTS')
    events = await system.get_events()
    print(len(events['events']))
    print()

    print('FIRST SYSTEM: SETTING TO "HOME"')
    events = await system.set_state(SystemStates.home)
    print(len(events['events']))


async def main() -> None:
    """Create the aiohttp session and run the example."""
    async with ClientSession() as websession:
        await run(websession)


async def run(websession: ClientSession):
    """Run."""
    try:
        await client_ss3(websession)
    except SimplipyError as err:
        print(err)


asyncio.get_event_loop().run_until_complete(main())
