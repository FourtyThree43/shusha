import asyncio

async def timer():
	for i in range(1, 31):
		print(f"{i}", end="\r")
		await asyncio.sleep(1)
	print()
		
asyncio.run(timer())