Response message


chat completions
```json
{
    "role": "user",
    "content": "hi there"
}

{
    "role": "assistant",
    "content": "i am doing well"
}
```

responses api

```json
{
    "type": "message",
    "role": "user",
    "content": [
        {
            "type": "input_text",
            "text": "hi there"
        }
    ]
}

{
    "type": "message",
    "role": "assistant",
    "content": [
        {
            "type": "output_text",
            "text": "i am doing well"
        }
    ]
}
```


----

