"""Run an example script to quickly test."""
import asyncio

from aiohttp import ClientSession

from simplipy import Client
from simplipy.errors import SimplipyError


async def client_ss2(websession: ClientSession) -> None:
    """Test a v2 SimpliSafe client."""
    print()
    print('CONNECTING TO CLIENT...')
    client = Client('glorianne5@comcast.net', websession)
    await client.authenticate_password("fddlupFELuPq3SzsJA6s")

    print('User ID: {0}'.format(client.user_id))
    print('Number of Systems: {0}'.format(len(client.systems)))

    system = client.systems[0]
    print('System #1 Properties: {0}'.format(system.__dict__))

    events = await system.get_events()
    print('System #1 Number of Events: {0}'.format((len(events['events']))))

    print()
    print('UPDATING SENSOR VALUES...')
    await system.update_sensors()
    for sensor in system.sensors:
        print(sensor.status)


async def main() -> None:
    """Create the aiohttp session and run the example."""
    async with ClientSession() as websession:
        await run(websession)


async def run(websession: ClientSession):
    """Run."""
    try:
        await client_ss2(websession)
    except SimplipyError as err:
        print(err)


asyncio.get_event_loop().run_until_complete(main())
