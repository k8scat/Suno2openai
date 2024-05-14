# -*- coding:utf-8 -*-
import datetime
import json
import os
import random
import string
import time

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from init_sql import create_database_and_table
from utils import generate_music, get_feed
import schemas
from utils import generate_music,get_feed
import asyncio
from suno.suno import SongsGen
from starlette.responses import StreamingResponse
from sql_uilts import DatabaseManager



app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def get_root():
    return schemas.Response()


BASE_URL = os.getenv('BASE_URL','https://studio-api.suno.ai')
DB_USER = os.getenv('DB_USER','')
DB_PASSWORD = os.getenv('DB_PASSWORD','')
DB_HOST = os.getenv('DB_HOST','')
DB_PORT = os.getenv('DB_PORT',3306)

def generate_random_string_async(length):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def generate_timestamp_async():
    return int(time.time())


async def generate_data(chat_user_message,chat_id,timeStamp):
    db_manager = DatabaseManager(DB_HOST, int(DB_PORT), DB_USER, DB_PASSWORD, DB_USER)

    while True:
        try:
            await db_manager.create_pool()
            cookie = await db_manager.get_non_working_cookie()
            break
        except:
            await create_database_and_table()
            db_manager.create_database_and_table()
    try:
        _return_ids = False
        _return_tags = False
        _return_title = False
        _return_prompt = False
        _return_image_url = False

        await db_manager.update_cookie_working(cookie, True)
        await db_manager.update_cookie_count(cookie, 1)

        token = SongsGen(cookie).self._get_auth_token()
        data = {
            "gpt_description_prompt": f"{chat_user_message}",
            "prompt": "",
            "mv": "chirp-v3-0",
            "title": "",
            "tags": ""
        }
        yield f"""data:"""+' '+f"""{json.dumps({"id": f"chatcmpl-{chat_id}", "object": "chat.completion.chunk", "model": "suno-v3", "created" : timeStamp, "choices": [{"index": 0, "delta": {"role":"assistant","content":""}, "finish_reason": None}]})}\n\n"""
        response = await generate_music(data=data, token=token)
        await asyncio.sleep(3)
        while True:
            try:
                response_clips = response["clips"]
                clip_ids = [clip["id"] for clip in response_clips]
                if not clip_ids:
                    return
                break
            except:
                pass

        # 使用 clip_ids 查询音频链接
        for clip_id in clip_ids:
            attempts = 0
            while attempts < 120:  # 限制尝试次数以避免无限循环
                now_data = await get_feed(ids=clip_id, token=token)
                more_information_ = now_data[0]['metadata']
                if type(now_data) == dict:
                    if now_data.get('detail') == 'Unauthorized':
                        link = f'https://audiopipe.suno.ai/?item_id={clip_id}'
                        link_data = f"\n **音乐链接**:{link}\n"
                        yield """data:"""+' '+f"""{json.dumps({"id": f"chatcmpl-{chat_id}", "object": "chat.completion.chunk", "model": "suno-v3", "created": timeStamp, "choices": [{"index": 0, "delta": {"content": link_data}, "finish_reason": None}]})}\n\n"""
                        break

                elif not _return_ids:
                    try:
                        song_id_1 = clip_ids[0]
                        song_id_2 = clip_ids[1]
                        song_id_text = (f""
                                        f"**歌曲id[1]** : {song_id_1}\n"
                                        f"**歌曲id[2]** : {song_id_2}\n"
                                        f"**完整歌曲链接（生成音乐链接后几分钟才生效）**: \n"
                                        f"歌曲① {'https://cdn1.suno.ai/'+song_id_1+'.mp3'} \n"
                                        f"歌曲② {'https://cdn1.suno.ai/'+song_id_2+'.mp3'} \n")
                        yield str(
                            f"""data:""" + ' ' + f"""{json.dumps({"id": f"chatcmpl-{chat_id}", "object": "chat.completion.chunk", "model": "suno-v3", "created": timeStamp, "choices": [{"index": 0, "delta": {"content": song_id_text}, "finish_reason": None}]})}\n\n""")

                        _return_ids = True
                    except:
                        pass

                elif not _return_title:
                    try:
                        title = now_data[0]["title"]
                        if title != '':
                            title_data = f"**歌名**:{title} \n"
                            yield """data:"""+' '+f"""{json.dumps({"id": f"chatcmpl-{chat_id}", "object": "chat.completion.chunk", "model": "suno-v3", "created": timeStamp, "choices": [{"index": 0, "delta": {"content": title_data}, "finish_reason": None}]})}\n\n"""
                            _return_title = True
                    except:
                        pass
                elif not _return_tags:
                    try:
                        tags = more_information_["tags"]
                        if tags is not None:
                            tags_data = f"**类型**:{tags} \n"
                            yield str(f"""data:"""+' '+f"""{json.dumps({"id": f"chatcmpl-{chat_id}", "object": "chat.completion.chunk", "model": "suno-v3", "created": timeStamp, "choices": [{"index": 0, "delta": {"content": tags_data}, "finish_reason": None}]})}\n\n""")
                            _return_tags = True
                    except:
                        pass
                elif not _return_prompt:
                    try:
                        prompt = more_information_["prompt"]
                        if prompt is not None:
                            prompt_data = f"**歌词**:{prompt} \n"
                            yield str(f"""data:"""+' '+f"""{json.dumps({"id": f"chatcmpl-{chat_id}", "object": "chat.completion.chunk", "model": "suno-v3", "created": timeStamp, "choices": [{"index": 0, "delta": {"content": prompt_data}, "finish_reason": None}]})}\n\n""")
                            _return_prompt = True
                    except:
                        pass


                elif not _return_image_url:
                    if now_data[0].get('image_url') is not None:

                        image_url_small_data = f"**图片链接:** ![封面图片_小]({now_data[0]['image_url']}) \n"
                        image_url_lager_data = f"**图片链接:** ![封面图片_大]({now_data[0]['image_large_url']}) \n"
                        yield f"""data:""" +' '+f"""{json.dumps({"id": f"chatcmpl-{chat_id}", "object": "chat.completion.chunk", "model": "suno-v3", "created": timeStamp, "choices": [{"index": 0, "delta": {"content": image_url_small_data}, "finish_reason": None}]})}\n\n"""
                        yield f"""data:""" +' '+f"""{json.dumps({"id": f"chatcmpl-{chat_id}", "object": "chat.completion.chunk", "model": "suno-v3", "created": timeStamp, "choices": [{"index": 0, "delta": {"content": image_url_lager_data}, "finish_reason": None}]})}\n\n"""
                        _return_image_url = True
                elif 'audio_url' in now_data[0]:
                    audio_url_ = now_data[0]['audio_url']
                    if audio_url_ != '':
                        audio_url_data = f"\n **音乐链接(临时)**:{audio_url_}"
                        yield f"""data:""" +' '+f"""{json.dumps({"id": f"chatcmpl-{chat_id}", "object": "chat.completion.chunk", "model": "suno-v3", "created": timeStamp, "choices": [{"index": 0, "delta": {"content": audio_url_data}, "finish_reason": None}]})}\n\n"""
                        break
                else:
                    content_wait = "."
                    yield f"""data:""" +' '+f"""{json.dumps({"id":f"chatcmpl-{chat_id}","object":"chat.completion.chunk","model":"suno-v3","created":timeStamp,"choices":[{"index":0,"delta":{"content":content_wait},"finish_reason":None}]})}\n\n"""
                    print(attempts)
                    print(now_data)
                    time.sleep(5)  # 等待5秒再次尝试
                    attempts += 1
        yield f"""data:"""+' '+f"""[DONE]\n\n"""
    except Exception as e:
        yield f"""data:"""+' '+f"""{json.dumps({"id":f"chatcmpl-{chat_id}","object":"chat.completion.chunk","model":"suno-v3","created":timeStamp,"choices":[{"index":0,"delta":{"content":str(e)},"finish_reason":None}]})}\n\n"""
        yield f"""data:"""+' '+f"""[DONE]\n\n"""
    finally:
        try:
            await db_manager.update_cookie_working(cookie, False)
        except:
            print('No sql')

@app.post("/v1/chat/completions")
async def get_last_user_message(data: schemas.Data):
    content_all = ''
    if DB_HOST == '' or DB_PASSWORD == '' or DB_USER == '':
        raise ValueError("BASE_URL is not set")
    else:
        chat_id = generate_random_string_async(29)
        timeStamp = generate_timestamp_async()
        last_user_content = None
        for message in reversed(data.messages):
            if message.role == "user":
                last_user_content = message.content
                break

        if last_user_content is None:
            raise HTTPException(status_code=400, detail="No user message found")
        headers = {
            'Cache-Control': 'no-cache',
            'Content-Type': 'text/event-stream',
            'Date': datetime.datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT'),
            'Server': 'uvicorn',
            'X-Accel-Buffering': 'no',
            'Transfer-Encoding': 'chunked'
        }

        if not data.stream:
            async for data_string in generate_data(last_user_content,chat_id,timeStamp):
                try:
                    json_data = data_string.split('data: ')[1].strip()

                    parsed_data = json.loads(json_data)
                    content = parsed_data['choices'][0]['delta']['content']
                    content_all += content
                except:
                    pass
            # input_tokens, output_tokens = calculate_token_costs(last_user_content,content_all,'gpt-3.5-turbo')
            json_string = {
                "id": f"chatcmpl-{chat_id}",
                "object": "chat.completion",
                "created": timeStamp,
                "model": "suno-v3",
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": content_all
                        },
                        "finish_reason": "stop"
                    }
                ],
                "usage": {
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0
                }
            }

            return json_string
        else:
            return StreamingResponse(generate_data(last_user_content,chat_id,timeStamp),headers=headers, media_type="text/event-stream")
