import asyncio
import os

import dotenv

dotenv.load_dotenv()  # pylint: disable=wrong-import-position

from lorgs.clients import discord


################################################################################
# Discord Client
#


async def test_exchange_code():
    """
    visit: https://discord.com/oauth2/authorize?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URL}&response_type=code&scope=identify
    and login to obtain a code
    """
    code = ""
    creds = await discord.exchange_code(code, redirect_uri="http://localhost:9001/login")
    print(creds)
    return creds


async def test_get_user_profile():
    """
    get creds via `auth.exchange_code`
    """
    creds = {
        "access_token": "ACCESS_TOKEN",
        "expires_in": 604800,
        "refresh_token": "<REFRESH_TOKEN>",
        "scope": "identify",
        "token_type": "Bearer",
    }
    access_token: str = creds["access_token"]  # type: ignore
    user_info = await discord.get_user_profile(access_token)
    print(user_info)


async def test_get_user_info():
    user_id = os.getenv("DISCORD_USER_ID")
    user_info = await discord.get_user_info(user_id)
    print(user_info)


async def test_get_member_info():
    user_id = os.getenv("DISCORD_USER_ID")
    server_id = os.getenv("DISCORD_SERVER_ID")
    member_info = await discord.get_member_info(server_id, user_id)
    print(member_info)


async def test_get_member_info_with_invalid_id():
    user_id = "123123123"
    server_id = os.getenv("DISCORD_SERVER_ID")
    member_info = await discord.get_member_info(server_id, user_id)
    print(member_info)


async def test_get_member_info_user_who_is_not_in_lorrgs():
    user_id = os.getenv("DISCORD_BOT_USER_ID")
    server_id = os.getenv("DISCORD_SERVER_ID")
    member_info = await discord.get_member_info(server_id, user_id)
    print(member_info)


################################################################################
# Auth Logic
#


async def test_get_member_roles():
    user_id = os.getenv("DISCORD_USER_ID")
    roles = await auth.get_member_roles(user_id)
    print(roles)


async def test_get_member_permissions():
    user_id = os.getenv("DISCORD_USER_ID")
    # user_id = "1321313"

    member_info = await auth.get_member_permissions(user_id)
    print(member_info)


async def main() -> None:
    # x = await test_exchange_code()
    # await test_get_user_profile()
    # await test_get_user_info()
    # await test_get_member_info()
    # await test_get_member_roles()
    # await test_get_member_info_user_who_is_not_in_lorrgs()
    # await test_get_member_info_with_invalid_id()

    # member_info = await discord.get_member_info(server_id, user_id)
    # print(member_info)
    # discord.api_request
    # /users/@me/guilds
    headers = {
        "Authorization": f"Bearer ...",
    }

    response = await discord.api_request(endpoint="users/@me/guilds", headers=headers)
    print(response)

    import json

    with open("/mnt/d/tmp.json", "w") as f:
        json.dump(response, f, indent=4)


if __name__ == "__main__":
    asyncio.run(main())
