import asyncio
import websockets
import json
import uuid

uuid_mapping = {}
previousLocsMap = {}
locationMap = {}
grid = [[0 for i in range(800)] for i in range(600)]
connected_users = set()

def getLineCoords(x1, y1, x2, y2, surround):
    x1 = x1 // 1
    x2 = x2 // 1
    y1 = y1 // 1
    y2 = y2 // 1
    coordinates = []
    dx = abs(x2 - x1)
    dy = abs(y2 - y1)
    sx = 1 if x1 < x2 else -1
    sy = 1 if y1 < y2 else -1
    err = dx - dy

    while x1 != x2 or y1 != y2:
        if surround == True:
            if tuple([x1, y1]) not in coordinates:
                coordinates.append([x1, y1])
            if tuple([x1 - 1, y1]) not in coordinates:
                coordinates.append(tuple([x1 - 1, y1]))
            if tuple([x1 + 1, y1]) not in coordinates:
                coordinates.append(tuple([x1 + 1, y1]))
            if tuple([x1, y1 - 1]) not in coordinates:
                coordinates.append(tuple([x1, y1 - 1]))
            if tuple([x1, y1 + 1]) not in coordinates:
                coordinates.append(tuple([x1, y1 + 1]))
        else:
            coordinates.append([x1, y1])
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x1 += sx
        if e2 < dx:
            err += dx
            y1 += sy

    coordinates.append((x2, y2))
    return coordinates

async def broadcast(data, exclude=None):
    data = json.dumps(data)
    for user in connected_users:
        if exclude != user:
            await user.send(data)

async def send_grid_data(websocket):
    message = json.dumps({"purpose": "load", "data": grid})
    await websocket.send(message)

async def handle_client(websocket):
    try:
        global grid
        connected_users.add(websocket)
        connection_uuid = str(uuid.uuid4())
        uuid_mapping[websocket] = connection_uuid
            
        print(f"User {websocket.remote_address} connected. Total users: {len(connected_users)}")
        await send_grid_data(websocket)
        while True:
            noBroadcast = False
            message = await websocket.recv()
            try:
                data = json.loads(message)
                data["sender"] = uuid_mapping.get(websocket)
                if data["purpose"] == "move":
                    socketUUID = uuid_mapping[websocket]
                    if socketUUID in previousLocsMap.keys():
                        prevLoc = previousLocsMap[socketUUID]
                        moveCoords = getLineCoords(int(prevLoc["x"]), int(prevLoc["y"]), int(data["x"]), int(data["y"]), False)
                        for i in moveCoords:
                            x = i[0]
                            y = i[1]
                            
                            if x > 799:
                                x = 799
                            if y > 599:
                                y = 599
                            if x < 0:
                                x = 0
                            if y < 0:
                                y = 0
                                
                            if grid[y][x] != 0 and grid[y][x] != socketUUID:
                                break
                            else:
                                previousLocsMap[socketUUID]["x"] = x
                                previousLocsMap[socketUUID]["y"] = y
                    else:
                        previousLocsMap[socketUUID] = {}
                        previousLocsMap[socketUUID]["x"] = data["x"]
                        previousLocsMap[socketUUID]["y"] = data["y"]
                        
                    data["x"] = previousLocsMap[socketUUID]["x"]
                    data["y"] = previousLocsMap[socketUUID]["y"]
                    
                    locationMap[socketUUID] = {"x": data["x"], "y": data["y"]}
                elif data["purpose"] == "draw":
                    if locationMap[socketUUID] == {"x": data["x2"], "y": data["y2"]}:
                        coords = getLineCoords(data["x1"], data["y1"], data["x2"], data["y2"], True)
                        for i in coords:
                            if grid[int(i[1])][int(i[0])] != 0 and grid[int(i[1])][int(i[0])] != uuid_mapping[websocket]:
                                pass
                            else:
                                grid[int(i[1])][int(i[0])] = uuid_mapping[websocket]
                    else:
                        noBroadcast = True
                elif data["purpose"] == "clear":
                    grid = [[0 for i in range(800)] for i in range(600)]
                if noBroadcast != True:
                    await broadcast(data)
            except:
                print(f"Invalid JSON received from {websocket.remote_address}: {message}")
    except:
        connected_users.remove(websocket)
        packet = {"purpose": "disconnect", "client": uuid_mapping[websocket]}
        await broadcast(packet)
        if uuid_mapping[websocket] in previousLocsMap.keys():
            previousLocsMap.pop(uuid_mapping[websocket], None)
        if uuid_mapping[websocket] in locationMap.keys():
            locationMap.pop(uuid_mapping[websocket], None)
        uuid_mapping.pop(websocket, None)
        print(f"User {websocket.remote_address} disconnected. Total users: {len(connected_users)}")
        
async def start_server():
    server = await websockets.serve(handle_client, "10.0.0.138", 1134)
    print(f"WebSocket server started on 10.0.0.138:1134.")

    try:
        await asyncio.Future()
    except asyncio.CancelledError:
        pass
    finally:
        server.close()

if __name__ == "__main__":
    asyncio.run(start_server())
