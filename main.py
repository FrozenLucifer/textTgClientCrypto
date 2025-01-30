import asyncio
from telethon import TelegramClient, events, sync
import diffi
from telethon.tl.types import *
import re
import crypto

api_id = 21520103
api_hash = 'db3a87249f0b17a38f44c38760081182'

client = TelegramClient('session_name', api_id, api_hash)
PREFIX = 'crypto:'


async def get_dialogs():
    dialogs: List[Dialog] = await client.get_dialogs(limit=100)
    for dialog in dialogs:
        if dialog.id > 0:
            print(f"{dialog.name[:20]:30} [id={dialog.id}]")


async def select_user():
    await get_dialogs()
    user_id = int(input("Введите id пользователя: "))
    return user_id


async def main():
    await client.start()
    await client.connect()
    user_id = await select_user()

    last_message = (await client.get_messages(user_id, 1))[0].message
    match = re.match(rf'{re.escape(PREFIX)}start request init (\d+), (\d+), (\d+)', last_message)
    if match:
        p = int(match.group(1))
        g = int(match.group(2))
        A = int(match.group(3))
        b = diffi.generate_prime(100)
        B = pow(g, b, p)
        K = pow(A, b, p)
        await client.send_message(user_id, PREFIX + f"start request accept {B}")
    else:
        p, g = diffi.generate_dh_parameters()
        a = diffi.generate_prime(100)
        A = pow(g, a, p)
        await client.send_message(user_id, PREFIX + f"start request init {p}, {g}, {A}")

        while True:
            messages = await client.get_messages(user_id, 1)
            if messages:
                last_message = messages[0].message
                match_accept = re.match(rf'{re.escape(PREFIX)}start request accept (\d+)', last_message)
                if match_accept:
                    B = int(match_accept.group(1))
                    break
            await asyncio.sleep(1)

        K = pow(B, a, p)

    print(f"Начат чат с пользователем {user_id}")

    async def send_messages(user_id, key):
        while True:
            message = await async_input("Введите сообщение для отправки: ")
            if message.lower() == '/exit':
                break
            encrypted_message = crypto.encrypt_message(message, key)
            await client.send_message(user_id, PREFIX + encrypted_message)

    @client.on(events.NewMessage(from_users=[user_id]))
    async def handle_new_message(event):
        message: str = event.message.message
        if message.startswith(PREFIX):
            message = message.removeprefix(PREFIX)
            message = crypto.decrypt_message(message, K)
        print(f"Получено сообщение: {message}")

    await asyncio.create_task(send_messages(user_id, K))
    await client.run_until_disconnected()


async def async_input(prompt):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, input, prompt)


if __name__ == '__main__':
    # get_dialogs()
    asyncio.run(main())
