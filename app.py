from fastapi import FastAPI, HTTPException, status
import httpx, json, redis

app = FastAPI()
redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)

redis_client.execute_command('CLIENT TRACKING', 'ON')


def get_from_redis(key):
    try:
        cached_value = redis_client.get(key)
        if cached_value:
            print('I have got from redis')
            return json.loads(cached_value)
        return None
    except Exception as e:
        print(f"Error while getting from Redis: {e}")
        return None


def set_to_redis(key, data):
    try:
        json_data = json.dumps(data)
        redis_client.setex(key, 10, json_data)
        print('I set to redis')
        return get_from_redis(key)
    except Exception as e:
        print(f"Error while setting to Redis: {e}")
        return None


@app.get("/{state_name}", response_model=dict)
async def get_weather(state_name: str):
    try:
        get_data = get_from_redis(state_name)
        if get_data:
            return get_data

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f'https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/\
                {state_name}?unitGroup=metric&key=PVF9N93EQLXVS8CRZKLH8BHN3&contentType=json'
            )
        
        if response.status_code == 200:
            return set_to_redis(state_name, response.json())

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bad Request"
        )

    except Exception as e:
        print(f"Error while processing the weather request for {state_name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app=app, host="0.0.0.0", port=8000)
