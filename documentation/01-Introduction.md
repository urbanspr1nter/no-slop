# Documentation Bootstrap

I maintain a personal project to do deep research for me. In preparation for this project, I told `Qwen3.5-122B-A10B` (Q4 quant) to compile a comprehensive document to build an AI coding agent like Claude Code, Opencode, etc.

Here is the original prompt. Don't judge me for bad grammar. At least I'm still writing :) 

```
Research and thoroughly document on the topic in how I can build a coding agent from scratch using a local LLM with vision capabilities.

I want it to behave like Claude Code, Opencode, aider, etc. where it can start doing work for you and run tools. 

I also want it to have do long term tasks like write an OS or perform lots of test and write summaries. 

It should also be able to interactively work on projects with the user. So turn-based chat is most likley required.

What do I need? What would be a simple architecture? Is Python good enough? How to create the TUI?

Do not write in bullet points summaries, but instead prefer conversational, detailed written material. 

Research as much as you need. You don't need to build it for me. I just want you to research for me in how I can get started building one with minimum functionality. I will be happy to see:

- TUI - how to keep command history, input commands, show diffs, etc.
- The LLM being able to show me diffs
- Basic tool calling loops
- Ability to edit files in various parts of it -- not just the beginning or the end of files
- Run shell commands
- Perform file system commands
- Search internet for more information

Note: For searching and scraping, I am already using a paid API to do this. So no worries, I think.

What else do you suggest for something minimal?

Be comprehensive, and don't worry about token usage. You have plenty. 

To save context, you can write data to files directly and then store into memory using tools. This will help you save context. Just make a note about storing information about a specific topic into memory within your context.
```

I did 2 versions. One that is "textbook" focused and the other "implementation" focused.

The resulting artifacts are stored in: `building-a-coding-agent`.

You can take a look at yourself. I will be using this guide and updating it to correct any inaccuracies as I go along.