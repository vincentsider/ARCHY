Directory Structure:

└── ./
    ├── examples
    │   ├── customer_service_streaming
    │   │   ├── configs
    │   │   │   ├── assistants
    │   │   │   │   └── user_interface
    │   │   │   │       └── assistant.json
    │   │   │   ├── tools
    │   │   │   │   ├── query_docs
    │   │   │   │   │   ├── handler.py
    │   │   │   │   │   └── tool.json
    │   │   │   │   ├── send_email
    │   │   │   │   │   ├── handler.py
    │   │   │   │   │   └── tool.json
    │   │   │   │   └── submit_ticket
    │   │   │   │       ├── handler.py
    │   │   │   │       └── tool.json
    │   │   │   ├── __init__.py
    │   │   │   ├── general.py
    │   │   │   ├── prompts.py
    │   │   │   └── swarm_tasks.json
    │   │   ├── data
    │   │   │   └── article_6233728.json
    │   │   ├── logs
    │   │   │   └── .gitkeep
    │   │   ├── src
    │   │   │   ├── evals
    │   │   │   │   └── eval_function.py
    │   │   │   ├── runs
    │   │   │   │   └── run.py
    │   │   │   ├── swarm
    │   │   │   │   ├── engines
    │   │   │   │   │   ├── assistants_engine.py
    │   │   │   │   │   ├── engine.py
    │   │   │   │   │   └── local_engine.py
    │   │   │   │   ├── assistants.py
    │   │   │   │   ├── conversation.py
    │   │   │   │   ├── swarm.py
    │   │   │   │   └── tool.py
    │   │   │   ├── tasks
    │   │   │   │   └── task.py
    │   │   │   ├── __init__.py
    │   │   │   ├── arg_parser.py
    │   │   │   ├── utils.py
    │   │   │   └── validator.py
    │   │   ├── tests
    │   │   │   ├── test_runs
    │   │   │   │   └── .gitkeep
    │   │   │   └── test_prompts.jsonl
    │   │   ├── .gitignore
    │   │   ├── docker-compose.yaml
    │   │   ├── main.py
    │   │   └── prep_data.py
    │   ├── support_bot
    │   │   ├── data
    │   │   │   └── article_6233728.json
    │   │   ├── __init__.py
    │   │   ├── customer_service.py
    │   │   ├── docker-compose.yaml
    │   │   ├── main.py
    │   │   ├── Makefile
    │   │   ├── prep_data.py
    │   │   ├── README.md
    │   │   └── requirements.txt
    │   ├── triage_agent
    │   │   ├── agents.py
    │   │   ├── evals_util.py
    │   │   ├── evals.py
    │   │   └── run.py
    │   ├── weather_agent
    │   │   ├── agents.py
    │   │   ├── evals.py
    │   │   └── run.py
    │   └── __init__.py
    ├── swarm
    │   ├── repl
    │   │   ├── __init__.py
    │   │   └── repl.py
    │   ├── __init__.py
    │   ├── core.py
    │   ├── types.py
    │   └── util.py
    ├── tests
    │   ├── __init__.py
    │   ├── mock_client.py
    │   ├── test_core.py
    │   └── test_util.py
    ├── pyproject.toml
    ├── README.md
    ├── SECURITY.md
    └── setup.cfg



---
File: /examples/customer_service_streaming/configs/assistants/user_interface/assistant.json
---

[
    {
        "model": "gpt-4-0125-preview",
        "description": "You are a user interface assistant that handles all interactions with the user. Call this assistant for general questions and when no other assistant is correct for the user query.",
        "log_flag": false,
        "tools":["query_docs",
        "submit_ticket",
        "send_email"],
        "planner": "sequential"
    }
]



---
File: /examples/customer_service_streaming/configs/tools/query_docs/handler.py
---

from openai import OpenAI
from src.utils import get_completion
import qdrant_client
import re

# # # Initialize connections
client = OpenAI()
qdrant = qdrant_client.QdrantClient(host='localhost')#, prefer_grpc=True)

# # Set embedding model
# # TODO: Add this to global config
EMBEDDING_MODEL = 'text-embedding-3-large'

# # # Set qdrant collection
collection_name = 'help_center'

# # # Query function for qdrant
def query_qdrant(query, collection_name, vector_name='article', top_k=5):
    # Creates embedding vector from user query
    embedded_query = client.embeddings.create(
        input=query,
        model=EMBEDDING_MODEL,
    ).data[0].embedding

    query_results = qdrant.search(
        collection_name=collection_name,
        query_vector=(
            vector_name, embedded_query
        ),
        limit=top_k,
    )

    return query_results


def query_docs(query):
    print(f'Searching knowledge base with query: {query}')
    query_results = query_qdrant(query,collection_name=collection_name)
    output = []

    for i, article in enumerate(query_results):
        title = article.payload["title"]
        text = article.payload["text"]
        url = article.payload["url"]

        output.append((title,text,url))

    if output:
        title, content, _ = output[0]
        response = f"Title: {title}\nContent: {content}"
        truncated_content = re.sub(r'\s+', ' ', content[:50] + '...' if len(content) > 50 else content)
        print('Most relevant article title:', truncated_content)
        return {'response': response}
    else:
        print('no results')
        return {'response': 'No results found.'}



---
File: /examples/customer_service_streaming/configs/tools/query_docs/tool.json
---

{
  "type": "function",
  "function": {
    "name": "query_docs",
    "description": "Tool to get information about OpenAI products to help users. This JUST querys the data, it does not respond to user.",
    "parameters": {
      "type": "object",
      "properties": {
        "query": {
          "type": "string",
          "description": "A detailed description of what the user wants to know."
        }
      },
      "required": [
        "query"
      ]
    }
  }
}



---
File: /examples/customer_service_streaming/configs/tools/send_email/handler.py
---

def send_email(email_address,message):
  response = f'email sent to: {email_address} with message: {message}'
  return {'response':response}
# def send_email_assistants(tool_id,address,message):
#   return {'response':f'email sent to {address} with message {message}'}



---
File: /examples/customer_service_streaming/configs/tools/send_email/tool.json
---

{
  "type": "function",
  "function": {
    "name": "send_email",
    "description": "Tool to send an email to any email address.",
    "parameters": {
      "type": "object",
      "properties": {
        "message": {
          "type": "string",
          "description": "Message content in the email. Make sure to use double quotes for any special characters."
        },
        "email_address": {
          "type": "string",
          "description": "Email address to send email to. Example: 'me@gmail.com'"
        }
      },
      "required": [
        "email_address", "message"
      ]
    }
  },
  "human_input":true
}



---
File: /examples/customer_service_streaming/configs/tools/submit_ticket/handler.py
---

def submit_ticket(description):
  return {'response':f'ticket created for {description}'}
def submit_ticket_assistants(description):
  return {'response':f'ticket created for {description}'}



---
File: /examples/customer_service_streaming/configs/tools/submit_ticket/tool.json
---

{
  "type": "function",
  "function": {
    "name": "submit_ticket",
    "description": "Tool to submit a help ticket for an issue or request for the OpenAI help center.",
    "parameters": {
      "type": "object",
      "properties": {
        "description": {
          "type": "string",
          "description": "Brief description of the technical details of the complaint."
        }
      },
      "required": [
        "description"
      ]
    }
  }
}



---
File: /examples/customer_service_streaming/configs/__init__.py
---




---
File: /examples/customer_service_streaming/configs/general.py
---

class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    GREY = '\033[90m'

test_root = 'tests'
test_file = 'test_prompts.jsonl'
tasks_path = 'configs/swarm_tasks.json'

#Options are 'assistants' or 'local'
engine_name = 'local'

max_iterations = 5

persist = False



---
File: /examples/customer_service_streaming/configs/prompts.py
---

TRIAGE_MESSAGE_PROMPT = "Given the following message: {}, select which assistant of the following is best suited to handle it: {}. Respond with JUST the name of the assistant, nothing else"
TRIAGE_SYSTEM_PROMPT = "You are an assistant who triages requests and selects the best assistant to handle that request."
EVAL_GROUNDTRUTH_PROMPT = "Given the following completion: {}, and the expected completion: {}, select whether the completion and expected completion are the same in essence. Correctness does not mean they are the same verbatim, but that the ANSWER is the same. For example: 'The answer, after calculating, is 4' and '4' would be the same. But 'it is 5' and 'the answer is 12' would be different. Respond with ONLY 'true' or 'false'"
EVAL_ASSISTANT_PROMPT = "Given the following assistant name: {}, and the expected assistant name: {}, select whether the assistants are the same. Minor formatting differences, or extra characters are OK, but the words should be the same. Respond with ONLY 'true' or 'false'"
EVAL_PLANNING_PROMPT = "Given the following plan: {}, and the expected plan: {}, select whether the plan and expected plan are the same in essence. Correctness does not mean they are the same verbatim, but that the content is the same with just minor formatting differences. Respond with ONLY 'true' or 'false'"
ITERATE_PROMPT = "Your task to complete is {}. You previously generated the following plan: {}. The steps completed, and the output of those steps, are here: {}. IMPORTANT: Given the outputs of the previous steps, use that to create a revised plan, using the following planning prompt."
EVALUATE_TASK_PROMPT = """Your task was {}. The steps you completed, and the output of those steps, are here: {}. IMPORTANT: Output the following, 'true' or 'false' if you successfully completed the task. Even if your plan changed from original plan, evaluate if the new plan and output
correctly satisfied the given task. Additionally, output a message for the user, explaining whya task was successfully completed, or why it failed. Example:
Task: "Tell a joke about cars. Translate it to Spanish"
Original Plan: [{{tool: "tell_joke", args: {{input: "cars"}}, {{tool: "translate", args: {{language: "Spanish"}}]
Steps Completed: [{{tool: "tell_joke", args: {{input: "cars", output: "Why did the car stop? It ran out of gas!"}}, {{tool: "translate", args: {{language: "Spanish", output: "¿Por qué se detuvo el coche? ¡Se quedó sin gas!"}}]
OUTPUT: ['true','The joke was successfully told and translated to Spanish.']
MAKE SURE THAT OUTPUT IS a list, bracketed by square brackets, with the first element being either 'true' or 'false', and the second element being a string message."""

# IMPORTANT: If you are missing
# any information, or do not have all the required arguments for the tools you are planning, just return your response in double quotes.
# to tell user what information you would need for the request.
#local_engine_vars
LOCAL_PLANNER_PROMPT = """
You are a planner for the Swarm framework.
Your job is to create a properly formatted JSON plan step by step, to satisfy the task given.
Create a list of subtasks based off the [TASK] provided. Your FIRST THOUGHT should be, do I need to call a tool here to answer
or fulfill the user's request. First, think through the steps of the plan necessary. Make sure to carefully look over the tools you are given access to to decide this.
If you are confident that you do not need a tool to respond, either just in conversation or to ask for clarification or more information, respond to the prompt in a concise, but conversational, tone in double quotes. Do not explain that you do not need a tool.
If you DO need tools, create a list of subtasks. Each subtask must be from within the [AVAILABLE TOOLS] list. DO NOT use any tools that are not in the list.
Make sure you have all information needed to call the tools you use in your plan.
Base your decisions on which tools to use from the description and the name and arguments of the tool.
Always output the arguments of the tool, even when arguments is an empty dictionary. MAKE SURE YOU USE ALL REQUIRED ARGUMENTS.
The plan should be as short as possible.

For example:

[AVAILABLE TOOLS]
{{
  "tools": [
    {{
      "type": "function",
      "function": {{
        "name": "lookup_contact_email",
        "description": "Looks up a contact and retrieves their email address",
        "parameters": {{
          "type": "object",
          "properties": {{
            "name": {{
              "type": "string",
              "description": "The name to look up"
            }}
          }},
          "required": ["name"]
        }}
      }}
    }},
    {{
      "type": "function",
      "function": {{
        "name": "email_to",
        "description": "Email the input text to a recipient",
        "parameters": {{
          "type": "object",
          "properties": {{
            "input": {{
              "type": "string",
              "description": "The text to email"
            }},
            "recipient": {{
              "type": "string",
              "description": "The recipient's email address. Multiple addresses may be included if separated by ';'."
            }}
          }},
          "required": ["input", "recipient"]
        }}
      }}
    }},
    {{
      "type": "function",
      "function": {{
        "name": "translate",
        "description": "Translate the input to another language",
        "parameters": {{
          "type": "object",
          "properties": {{
            "input": {{
              "type": "string",
              "description": "The text to translate"
            }},
            "language": {{
              "type": "string",
              "description": "The language to translate to"
            }}
          }},
          "required": ["input", "language"]
        }}
      }}
    }},
    {{
      "type": "function",
      "function": {{
        "name": "summarize",
        "description": "Summarize input text",
        "parameters": {{
          "type": "object",
          "properties": {{
            "input": {{
              "type": "string",
              "description": "The text to summarize"
            }}
          }},
          "required": ["input"]
        }}
      }}
    }},
    {{
      "type": "function",
      "function": {{
        "name": "joke",
        "description": "Generate a funny joke",
        "parameters": {{
          "type": "object",
          "properties": {{
            "input": {{
              "type": "string",
              "description": "The input to generate a joke about"
            }}
          }},
          "required": ["input"]
        }}
      }}
    }},
    {{
      "type": "function",
      "function": {{
        "name": "brainstorm",
        "description": "Brainstorm ideas",
        "parameters": {{
          "type": "object",
          "properties": {{
            "input": {{
              "type": "string",
              "description": "The input to brainstorm about"
            }}
          }},
          "required": ["input"]
        }}
      }}
    }},
    {{
      "type": "function",
      "function": {{
        "name": "poe",
        "description": "Write in the style of author Edgar Allen Poe",
        "parameters": {{
          "type": "object",
          "properties": {{
            "input": {{
              "type": "string",
              "description": "The input to write about"
            }}
          }},
          "required": ["input"]
        }}
      }}
    }}
  ]
}}

[TASK]
"Tell a joke about cars. Translate it to Spanish"

[OUTPUT]
[
    {{"tool": "joke","args":{{"input": "cars"}}}},
    {{"tool": "translate", "args": {{"language": "Spanish"}}
  ]

[TASK]
"Tomorrow is Valentine's day. I need to come up with a few date ideas. She likes Edgar Allen Poe so write using his style. E-mail these ideas to my significant other. Translate it to French."

[OUTPUT]
[{{"tool": "brainstorm","args":{{"input": "Valentine's Day Date Ideas"}}}},
    {{"tool": "poe", "args": {{}}}},
    {{"tool": "email_to", "args": {{"recipient": "significant_other@example.com"}},
    {{"tool": "translate", "args": {{"language": "French"}}]

[AVAILABLE TOOLS]
{tools}

[TASK]
{task}

[OUTPUT]
"""



---
File: /examples/customer_service_streaming/configs/swarm_tasks.json
---

[
  {
    "description": "What is the square root of 16?"
  },
  {
    "description": "Is phone verification required for new OpenAI account creation or ChatGPT usage",
    "evaluate": true
  },
  {
    "description": "How many free tokens do I get when I sign up for an OpenAI account? Send an email to me@gmail.com containing that answer",
    "iterate": true,
    "evaluate": true
  }
]



---
File: /examples/customer_service_streaming/data/article_6233728.json
---

{"text": "Introduction\n============\n\n\n\u200bSince releasing the Answers endpoint in beta last year, we\u2019ve developed new methods that achieve better results for this task. As a result, we\u2019ll be removing the Answers endpoint from our documentation and removing access to this endpoint on December 3, 2022 for all organizations. New accounts created after June 3rd will not have access to this endpoint.\n\n\n\nWe strongly encourage developers to switch over to newer techniques which produce better results, outlined below.\n\n\n\nCurrent documentation\n---------------------\n\n\n<https://beta.openai.com/docs/guides/answers> \n\n\n<https://beta.openai.com/docs/api-reference/answers>\n\n\n\nOptions\n=======\n\n\nAs a quick review, here are the high level steps of the current Answers endpoint:\n\n\n\n\n![](https://openai.intercom-attachments-7.com/i/o/524217540/51eda23e171f33f1b9d5acff/rM6ZVI3XZ2CpxcEStmG5mFy6ATBCskmX2g3_GPmeY3FicvrWfJCuFOtzsnbkpMQe-TQ6hi5j1BV9cFo7bCDcsz8VWxFfeOnC1Gb4QNaeVYtJq4Qtg76SBOLLk-jgHUA8mWZ0QgOuV636UgcvMA)All of these options are also outlined [here](https://github.com/openai/openai-cookbook/tree/main/transition_guides_for_deprecated_API_endpoints)\n\n\n\nOption 1: Transition to Embeddings-based search (recommended)\n-------------------------------------------------------------\n\n\nWe believe that most use cases will be better served by moving the underlying search system to use a vector-based embedding search. The major reason for this is that our current system used a bigram filter to narrow down the scope of candidates whereas our embeddings system has much more contextual awareness. Also, in general, using embeddings will be considerably lower cost in the long run. If you\u2019re not familiar with this, you can learn more by visiting our [guide to embeddings](https://beta.openai.com/docs/guides/embeddings/use-cases).\n\n\n\nIf you\u2019re using a small dataset (<10,000 documents), consider using the techniques described in that guide to find the best documents to construct a prompt similar to [this](#h_89196129b2). Then, you can just submit that prompt to our [Completions](https://beta.openai.com/docs/api-reference/completions) endpoint.\n\n\n\nIf you have a larger dataset, consider using a vector search engine like [Pinecone](https://share.streamlit.io/pinecone-io/playground/beyond_search_openai/src/server.py) or [Weaviate](https://weaviate.io/developers/weaviate/current/retriever-vectorizer-modules/text2vec-openai.html) to power that search.\n\n\n\nOption 2: Reimplement existing functionality\n--------------------------------------------\n\n\nIf you\u2019d like to recreate the functionality of the Answers endpoint, here\u2019s how we did it. There is also a [script](https://github.com/openai/openai-cookbook/blob/main/transition_guides_for_deprecated_API_endpoints/answers_functionality_example.py) that replicates most of this functionality.\n\n\n\nAt a high level, there are two main ways you can use the answers endpoint: you can source the data from an uploaded file or send it in with the request.\n\n\n\n**If you\u2019re using the document parameter**\n------------------------------------------\n\n\nThere\u2019s only one step if you provide the documents in the Answers API call.\n\n\n\nHere\u2019s roughly the steps we used: \n\n\n* Construct the prompt [with this format.](#h_89196129b2)\n* Gather all of the provided documents. If they fit in the prompt, just use all of them.\n* Do an [OpenAI search](https://beta.openai.com/docs/api-reference/searches) (note that this is also being deprecated and has a [transition guide](https://app.intercom.com/a/apps/dgkjq2bp/articles/articles/6272952/show)) where the documents are the user provided documents and the query is the query from above. Rank the documents by score.\n* In order of score, attempt to add Elastic search documents until you run out of space in the context.\n* Request a completion with the provided parameters (logit\\_bias, n, stop, etc)\n\n\nThroughout all of this, you\u2019ll need to check that the prompt\u2019s length doesn\u2019t exceed [the model's token limit](https://beta.openai.com/docs/engines/gpt-3). To assess the number of tokens present in a prompt, we recommend <https://huggingface.co/docs/transformers/model_doc/gpt2#transformers.GPT2TokenizerFast>. \n\n\n\nIf you're using the file parameter\n----------------------------------\n\n\nStep 1: upload a jsonl file\n\n\n\nBehind the scenes, we upload new files meant for answers to an Elastic search cluster. Each line of the jsonl is then submitted as a document.\n\n\n\nIf you uploaded the file with the purpose \u201canswers,\u201d we additionally split the documents on newlines and upload each of those chunks as separate documents to ensure that we can search across and reference the highest number of relevant text sections in the file.\n\n\n\nEach line requires a \u201ctext\u201d field and an optional \u201cmetadata\u201d field.\n\n\n\nThese are the Elastic search settings and mappings for our index:\n\n\n\n[Elastic searching mapping](https://www.elastic.co/guide/en/elasticsearch/reference/current/mapping.html): \n\n\n\n```\n{  \n    \"properties\": {  \n        \"document\": {\"type\": \"text\", \"analyzer\": \"standard_bigram_analyzer\"}, -> the \u201ctext\u201d field  \n        \"metadata\": {\"type\": \"object\", \"enabled\": False}, -> the \u201cmetadata\u201d field  \n    }  \n}\n```\n\n\n[Elastic search analyzer](https://www.elastic.co/guide/en/elasticsearch/reference/current/mapping.html):\n\n\n\n```\n{  \n    \"analysis\": {  \n        \"analyzer\": {  \n            \"standard_bigram_analyzer\": {  \n                \"type\": \"custom\",  \n                \"tokenizer\": \"standard\",  \n                \"filter\": [\"lowercase\", \"english_stop\", \"shingle\"],  \n            }  \n        },  \n        \"filter\": {\"english_stop\": {\"type\": \"stop\", \"stopwords\": \"_english_\"}},  \n    }  \n}\n```\n\n\nAfter that, we performed [standard Elastic search search calls](https://elasticsearch-py.readthedocs.io/en/v8.2.0/api.html#elasticsearch.Elasticsearch.search) and used `max\\_rerank` to determine the number of documents to return from Elastic search.\n\n\n\nStep 2: Search\n\n\nHere\u2019s roughly the steps we used. Our end goal is to create a [Completions](https://beta.openai.com/docs/api-reference/completions) request [with this format](#h_89196129b2). It will look very similar to [Documents](#h_cb1d8a8d3f)\n\n\n\nFrom there, our steps are: \n\n\n* Start with the `experimental\\_alternative\\_question` or, if that's not provided, what\u2019s in the `question` field. Call that the query.\n* Query Elastic search for `max\\_rerank` documents with query as the search param.\n* Take those documents and do an [OpenAI search](https://beta.openai.com/docs/api-reference/searches) on them where the entries from Elastic search are the docs, and the query is the query that you used above. Use the score from the search to rank the documents.\n* In order of score, attempt to add Elastic search documents until you run out of space in the prompt.\n* Request an OpenAI completion with the provided parameters (logit\\_bias, n, stop, etc). Return that answer to the user.\n\n\nCompletion Prompt\n-----------------\n\n\n\n```\n===  \nContext: #{{ provided examples_context }}  \n===  \nQ: example 1 question  \nA: example 1 answer  \n---  \nQ: example 2 question  \nA: example 2 answer  \n(and so on for all examples provided in the request)   \n===  \nContext: #{{ what we return from Elasticsearch }}  \n===  \nQ: #{{ user provided question }}   \nA:\n```\n", "title": "Answers Transition Guide", "article_id": "6233728", "url": "https://help.openai.com/en/articles/6233728-answers-transition-guide"}


---
File: /examples/customer_service_streaming/logs/.gitkeep
---




---
File: /examples/customer_service_streaming/src/evals/eval_function.py
---

from src.utils import get_completion
from configs.prompts import EVAL_GROUNDTRUTH_PROMPT
import json
import re
import ast
from openai import OpenAI

class EvalFunction:

  def __init__(self, client, plan, task):
        self.client = client
        self.eval_function =  getattr(self, task.eval_function, None)
        self.task = task
        self.groundtruth = task.groundtruth
        self.plan = plan

  def default(self):
    response = get_completion(self.client, [{"role": "user", "content": EVAL_GROUNDTRUTH_PROMPT.format(self.plan, self.groundtruth)}])
    if response.content.lower() == 'true':
        return True
    return False
    
  def numeric(self):
    number_pattern = r'\d+'
    response = self.plan['step'][-1]
    # Find all occurrences of numbers in the sentence
    numbers = re.findall(number_pattern, response)
    print(f"Number(s) to compare: {numbers}")
    try:
        ground_truth = ast.literal_eval(self.groundtruth)
    except:
       print(f"Ground truth is not numeric: {self.groundtruth}")
       return False
    try:
        for n in numbers:
            if int(ground_truth) == int(n) or float(ground_truth) == float(n):
                return True
    except:
        print(f"Error in comparing numbers: {numbers}")
    return False

  def name(self):
    extract_name_prompt = "You will be provided with a sentence. Your goal is to extract the full names you see in the sentence. Return the names as an array of strings."
    response = self.plan['step'][-1]
    completion_result = self.client.chat.completions.create(
       model="gpt-4-turbo-preview",
       max_tokens=100,
       temperature=0,
       messages=[
        {"role": "system",
         "content": extract_name_prompt
         },
         {"role": "user", "content": f"SENTENCE:\n{response}"}]
    )
    name_extract = completion_result.choices[0].message.content
    print(f"Name extracted: {name_extract}")
    try:
       names = ast.literal_eval(name_extract)
       ground_truth = self.groundtruth
       for n in names:
          if n.lower == ground_truth.lower():
              return True
    except:
       print(f"Issue with extracted names: {name_extract}")
    return False
  
  def evaluate(self):
    return self.eval_function()


---
File: /examples/customer_service_streaming/src/runs/run.py
---

from configs.prompts import LOCAL_PLANNER_PROMPT
from src.utils import get_completion
import json

class Run:
    def __init__(self,assistant,request,client):
        self.assistant = assistant
        self.request = request
        self.client = client
        self.status = None
        self.response = None


    def initiate(self, planner):
        self.status = 'in_progress'
        if planner=='sequential':
            plan = self.generate_plan()
            return plan

    def generate_plan(self,task=None):
        if not task:
            task = self.request
        completion = get_completion(self.client,[{'role':'user','content':LOCAL_PLANNER_PROMPT.format(tools=self.assistant.tools,task=task)}])
        response_string = completion.content
        #Parse out just list in case
        try: # see if plan
            start_pos = response_string.find('[')
            end_pos = response_string.rfind(']')

            if start_pos != -1 and end_pos != -1 and start_pos < end_pos:
                response_truncated = response_string[start_pos:end_pos+1]
                response_formatted = json.loads(response_truncated)
                return response_formatted
            else:
                try:
                    response_formatted = json.loads(response_string)
                    return response_formatted
                except:
                    return "Response not in correct format"
        except:
            return response_string



---
File: /examples/customer_service_streaming/src/swarm/engines/assistants_engine.py
---

import json
import os
from src.utils import get_completion
from configs.general import Colors
from configs.prompts import TRIAGE_SYSTEM_PROMPT, TRIAGE_MESSAGE_PROMPT, EVALUATE_TASK_PROMPT
import time
from src.swarm.assistants import Assistant
from src.tasks.task import EvaluationTask
from openai import OpenAI
import importlib


class AssistantsEngine:
    def __init__(self,client,tasks):
        self.client = client
        self.assistants = []
        self.tasks = tasks
        self.thread = self.initialize_thread()


    def initialize_thread(self):
        # Create a Thread for the user's conversation
        thread = self.client.beta.threads.create()
        return thread

    def reset_thread(self):
        # Create a Thread for the user's conversation
        self.thread = self.client.beta.threads.create()

    def load_all_assistants(self):
        base_path = 'assistants'
        tools_base_path = 'tools'

        # Load individual tool definitions from the tools directory
        tool_defs = {}
        for tool_dir in os.listdir(tools_base_path):
            if '__pycache__' in tool_dir:
                continue
            tool_dir_path = os.path.join(tools_base_path, tool_dir)
            if os.path.isdir(tool_dir_path):
                tool_json_path = os.path.join(tool_dir_path, 'tool.json')
                if os.path.isfile(tool_json_path):
                    with open(tool_json_path, 'r') as file:
                        # Assuming the JSON file contains a list of tool definitions
                        tool_def = json.load(file)
                        tool_defs[tool_def['function']['name']] = tool_def['function']
        # Load assistants and their tools
        for assistant_dir in os.listdir(base_path):
            if '__pycache__' in assistant_dir:
                continue
            assistant_config_path = os.path.join(base_path, assistant_dir, "assistant.json")
            if os.path.exists(assistant_config_path):
                with open(assistant_config_path, "r") as file:
                    assistant_config = json.load(file)[0]

                    assistant_name = assistant_config.get('name', assistant_dir)
                    log_flag = assistant_config.pop('log_flag', False)

                    # List of tool names from the assistant's config
                    assistant_tools_names = assistant_config.get('tools', [])

                    # Build the list of tool definitions for this assistant
                    assistant_tools = [tool_defs[name] for name in assistant_tools_names if name in tool_defs]

                    # Create or update the assistant instance
                    existing_assistants = self.client.beta.assistants.list()
                    loaded_assistant = next((a for a in existing_assistants if a.name == assistant_name), None)

                    if loaded_assistant:
                        assistant_tools = [{'type': 'function', 'function': tool_defs[name]} for name in assistant_tools_names if name in tool_defs]
                        assistant_config['tools'] = assistant_tools
                        assistant_config['name']=assistant_name

                        loaded_assistant = self.client.beta.assistants.create(**assistant_config)
                        print(f"Assistant '{assistant_name}' created.\n")

                    asst_object = Assistant(name=assistant_name, log_flag=log_flag, instance=loaded_assistant, tools=assistant_tools)
                    self.assistants.append(asst_object)


    def initialize_and_display_assistants(self):
            """
            Loads all assistants and displays their information.
            """
            self.load_all_assistants()

            for asst in self.assistants:
                print(f'\n{Colors.HEADER}Initializing assistant:{Colors.ENDC}')
                print(f'{Colors.OKBLUE}Assistant name:{Colors.ENDC} {Colors.BOLD}{asst.name}{Colors.ENDC}')
                if asst.instance and hasattr(asst.instance, 'tools'):
                    print(f'{Colors.OKGREEN}Tools:{Colors.ENDC} {asst.instance.tools} \n')
                else:
                    print(f"{Colors.OKGREEN}Tools:{Colors.ENDC} Not available \n")


    def get_assistant(self, assistant_name):

        for assistant in self.assistants:
            if assistant.name == assistant_name:
                return assistant
        print('No assistant found')
        return None

    def triage_request(self, message, test_mode):
        """
        Analyze the user message and delegate it to the appropriate assistant.
        """
        #determine the appropriate assistant for the message
        assistant_name = self.determine_appropriate_assistant(message)
        assistant = self.get_assistant(assistant_name)

        if assistant:
            print(
            f"{Colors.OKGREEN}\nSelected Assistant:{Colors.ENDC} {Colors.BOLD}{assistant.name}{Colors.ENDC}"
            )
            assistant.add_assistant_message('Selected Assistant: '+assistant.name)
            return assistant
        #else
        if not test_mode:
            print('No assistant found')
        return None


    def determine_appropriate_assistant(self, message):
        triage_message = [{"role": "system", "content": TRIAGE_SYSTEM_PROMPT}]
        triage_message.append(
            {
                "role": "user",
                "content": TRIAGE_MESSAGE_PROMPT.format(message, [asst.instance for asst in self.assistants]),
            }
        )
        response = get_completion(self.client, triage_message)
        return response.content


    def run_request(self, request, assistant,test_mode):
        """
        Run the request with the selected assistant and monitor its status.
        """
        # Add message to thread
        self.client.beta.threads.messages.create(
            thread_id=self.thread.id,
            role="user",
            content=request
        )

        # Initialize run
        run = self.client.beta.threads.runs.create(
            thread_id=self.thread.id,
            assistant_id=assistant.instance.id
        )

        # Monitor the run status in a loop
        while True:
            run = self.client.beta.threads.runs.retrieve(
                thread_id=self.thread.id,
                run_id=run.id
            )

            if run.status in ["queued", "in_progress"]:
                time.sleep(2)  # Wait before checking the status again
                if not test_mode:
                    print('waiting for run')
            elif run.status == "requires_action":
                tool_call = run.required_action.submit_tool_outputs.tool_calls[0]
                self.handle_tool_call(tool_call, run)
                # Re-submitting the tool outputs and continue the loop

            elif run.status in ["completed","expired", "cancelling", "cancelled", "failed"]:
                if not test_mode:
                    print(f'\nrun {run.status}')
                break

        if assistant.log_flag:
            self.store_messages()
        # Retrieve and return the response (only if completed)
        messages = self.client.beta.threads.messages.list(thread_id=self.thread.id)
        assistant_response = next((msg for msg in messages.data if msg.role == 'assistant' and msg.content), None)


        if assistant_response:
            assistant_response_text = assistant_response.content[0].text.value
            if not test_mode:
                print(f"{Colors.RED}Response:{Colors.ENDC} {assistant_response_text}", "\n")
            return assistant_response_text
        return "No response from the assistant."


    def handle_tool_call(self, tool_call, run):
        tool_name = tool_call.function.name
        tool_dir = os.path.join(os.getcwd(), 'tools', tool_name)
        handler_path = os.path.join(tool_dir, 'handler.py')

        # Dynamically import the handler function from the handler.py file
        if os.path.isfile(handler_path):
            spec = importlib.util.spec_from_file_location(f"{tool_name}_handler", handler_path)
            tool_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(tool_module)
            tool_handler = getattr(tool_module, tool_name+ '_assistants')

            # Prepare the arguments for the handler function
            handler_args = {'tool_id': tool_call.id}
            tool_args = json.loads(tool_call.function.arguments)
            for arg_name, arg_value in tool_args.items():
                if arg_value is not None:
                    handler_args[arg_name] = arg_value

            # Call the handler function with arguments
            print(f"{Colors.HEADER}Running Tool:{Colors.ENDC} {tool_name}")
            print(handler_args)
            tool_response = tool_handler(**handler_args)

            # Submit the tool response back to the thread
            self.client.beta.threads.runs.submit_tool_outputs(
                thread_id=self.thread.id,
                run_id=run.id,
                tool_outputs=[
                    {
                        "tool_call_id": tool_call.id,
                        "output": json.dumps({"result": tool_response}),
                    }
                ],
            )
        else:
            print(f"No handler found for tool {tool_name}")

    def store_messages(self, filename="threads/thread_data.json"):

        thread = self.client.beta.threads.messages.list(thread_id=self.thread.id)
        # Extract the required fields from each message in the thread
        messages = []
        for message in thread.data:
            role = message.role
            run_id = message.run_id
            assistant_id = message.assistant_id
            thread_id = message.thread_id
            created_at = message.created_at
            content_value = message.content[0].text.value
            messages.append({
                'role': role,
                'run_id': run_id,
                'assistant_id': assistant_id,
                'thread_id': thread_id,
                'created_at': created_at,
                'content': content_value
            })
        try:
            with open(filename, 'r') as file:
                existing_threads = json.load(file)

        except:
            existing_threads = []


        # Convert the OpenAI object to a serializable format (e.g., a dictionary)
        # Append new threads
        existing_threads.append(messages)
        # Save back to the file
        try:
            with open(filename, 'w') as file:
                json.dump(existing_threads, file, indent=4)
        except Exception as e:
            print(f"Error while saving to file: {e}")


    def run_task(self, task,test_mode):
            """
            Processes a given task. If the assistant is set to 'auto', it determines the appropriate
            assistant using triage_request. Otherwise, it uses the specified assistant.
            """
            if not test_mode:
                print(
            f"{Colors.OKCYAN}User Query:{Colors.ENDC} {Colors.BOLD}{task.description}{Colors.ENDC}"
                )
            else:
                print(
            f"{Colors.OKCYAN}Test:{Colors.ENDC} {Colors.BOLD}{task.description}{Colors.ENDC}"
                )

            if task.assistant == 'auto':
                # Triage the request to determine the appropriate assistant
                assistant = self.triage_request(task.description,test_mode)
            else:
                # Fetch the specified assistant
                assistant = self.get_assistant(task.assistant)
                print(
                f"{Colors.OKGREEN}\nSelected Assistant:{Colors.ENDC} {Colors.BOLD}{assistant.name}{Colors.ENDC}"
                )

            if test_mode:
                task.assistant = assistant.name if assistant else "None"
            if not assistant:
                if not test_mode:
                    print(f"No suitable assistant found for the task: {task.description}")
                return None

            # Run the request with the determined or specified assistant
            self.reset_thread()
            return self.run_request(task.description, assistant,test_mode)

    def deploy(self, client,test_mode=False,test_file_path=None):
        """
        Processes all tasks in the order they are listed in self.tasks.
        """
        #Initialize swarm first
        self.client = client
        if test_mode and test_file_path:
            print("\nTesting the swarm\n\n")
            self.load_test_tasks(test_file_path)
        else:
            print("\n🐝🐝🐝 Deploying the swarm 🐝🐝🐝\n\n")

        self.initialize_and_display_assistants()
        total_tests = 0
        groundtruth_tests = 0
        assistant_tests = 0
        for task in self.tasks:
            output = self.run_task(task,test_mode)

            if test_mode and hasattr(task, 'groundtruth'):
                total_tests += 1

                response = get_completion(self.client,[{"role":"user","content":EVALUATE_TASK_PROMPT.format(output,task.groundtruth)}])

                if response.content=='True':
                    groundtruth_tests += 1
                    print(f"{Colors.OKGREEN}✔ Groundtruth test passed for: {Colors.ENDC}{task.description}{Colors.OKBLUE}. Expected: {Colors.ENDC}{task.groundtruth}{Colors.OKBLUE}, Got: {Colors.ENDC}{output}{Colors.ENDC}")
                else:
                    print(f"{Colors.RED}✘ Test failed for: {Colors.ENDC}{task.description}{Colors.OKBLUE}. Expected: {Colors.ENDC}{task.groundtruth}{Colors.OKBLUE}, Got: {Colors.ENDC}{output}{Colors.ENDC}")

                if task.assistant==task.expected_assistant:
                    print(f"{Colors.OKGREEN}✔ Correct assistant assigned for: {Colors.ENDC}{task.description}{Colors.OKBLUE}. Expected: {Colors.ENDC}{task.expected_assistant}{Colors.OKBLUE}, Got: {Colors.ENDC}{task.assistant}{Colors.ENDC}\n")
                    assistant_tests += 1
                else:
                    print(f"{Colors.RED}✘ Incorrect assistant assigned for: {Colors.ENDC}{task.description}{Colors.OKBLUE}. Expected: {Colors.ENDC}{task.expected_assistant}{Colors.OKBLUE}, Got: {Colors.ENDC}{task.assistant}{Colors.ENDC}\n")

        if test_mode:
            print(f"\n{Colors.OKGREEN}Passed {groundtruth_tests} groundtruth tests out of {total_tests} tests. Success rate: {groundtruth_tests/total_tests*100}%{Colors.ENDC}\n")
            print(f"{Colors.OKGREEN}Passed {assistant_tests} assistant tests out of {total_tests} tests. Success rate: {groundtruth_tests/total_tests*100}%{Colors.ENDC}\n")
            print("Completed testing the swarm\n\n")
        else:
            print("🍯🐝🍯 Swarm operations complete 🍯🐝🍯\n\n")



    def load_test_tasks(self, test_file_path):
        self.tasks = []  # Clear any existing tasks
        with open(test_file_path, 'r') as file:
            for line in file:
                test_case = json.loads(line)
                task = EvaluationTask(description=test_case['text'],
                            assistant=test_case.get('assistant', 'auto'),
                            groundtruth=test_case['groundtruth'],
                            expected_assistant=test_case['expected_assistant'])
                self.tasks.append(task)



---
File: /examples/customer_service_streaming/src/swarm/engines/engine.py
---

# engine.py
class Engine:
    def __init__(self, tasks,engine):
      self.engine = engine



---
File: /examples/customer_service_streaming/src/swarm/engines/local_engine.py
---

import importlib
import json
import os
from configs.prompts import TRIAGE_MESSAGE_PROMPT, TRIAGE_SYSTEM_PROMPT, EVAL_GROUNDTRUTH_PROMPT, EVAL_PLANNING_PROMPT, ITERATE_PROMPT
from src.utils import get_completion, is_dict_empty
from configs.general import Colors, max_iterations
from src.swarm.assistants import Assistant
from src.swarm.tool import Tool
from src.tasks.task import EvaluationTask
from src.runs.run import Run



class LocalEngine:
    def __init__(self, client, tasks, persist=False):
        self.client = client
        self.assistants = []
        self.last_assistant = None
        self.persist = persist
        self.tasks = tasks
        self.tool_functions = []
        self.global_context = {}

    def load_tools(self):
        tools_path = 'configs/tools'

        self.tool_functions = []
        for tool_dir in os.listdir(tools_path):
            dir_path = os.path.join(tools_path, tool_dir)
            if os.path.isdir(dir_path):
                for tool_name in os.listdir(dir_path):
                    if tool_name.endswith('.json'):
                        with open(os.path.join(dir_path, tool_name), 'r') as file:
                            try:
                                tool_def = json.load(file)
                                tool = Tool(type=tool_def['type'], function=tool_def['function'], human_input=tool_def.get('human_input', False))
                                self.tool_functions.append(tool)
                            except json.JSONDecodeError as e:
                                print(f"Error decoding JSON for tool {tool_name}: {e}")

    def load_all_assistants(self):
        base_path = 'configs/assistants'
        self.load_tools()
        tool_defs = {tool.function.name: tool.function.dict() for tool in self.tool_functions}

        for assistant_dir in os.listdir(base_path):
            if '__pycache__' in assistant_dir:
                continue
            assistant_config_path = os.path.join(base_path, assistant_dir, "assistant.json")
            if os.path.exists(assistant_config_path):
                try:
                    with open(assistant_config_path, "r") as file:
                        assistant_config = json.load(file)[0]
                        assistant_tools_names = assistant_config.get('tools', [])
                        assistant_name = assistant_config.get('name', assistant_dir)
                        assistant_tools = [tool for tool in self.tool_functions if tool.function.name in assistant_tools_names]

                        log_flag = assistant_config.pop('log_flag', False)
                        sub_assistants = assistant_config.get('assistants', None)
                        planner = assistant_config.get('planner', 'sequential') #default is sequential
                        print(f"Assistant '{assistant_name}' created.\n")
                        asst_object = Assistant(name=assistant_name, log_flag=log_flag, instance=None, tools=assistant_tools, sub_assistants=sub_assistants, planner=planner)
                        asst_object.initialize_history()
                        self.assistants.append(asst_object)
                except (IOError, json.JSONDecodeError) as e:
                    print(f"Error loading assistant configuration from {assistant_config_path}: {e}")


    def initialize_and_display_assistants(self):
            """
            Loads all assistants and displays their information.
            """
            self.load_all_assistants()
            self.initialize_global_history()

            for asst in self.assistants:
                print(f'\n{Colors.HEADER}Initializing assistant:{Colors.ENDC}')
                print(f'{Colors.OKBLUE}Assistant name:{Colors.ENDC} {Colors.BOLD}{asst.name}{Colors.ENDC}')
                if asst.tools:
                    print(f'{Colors.OKGREEN}Tools:{Colors.ENDC} {[tool.function.name for tool in asst.tools]} \n')
                else:
                    print(f"{Colors.OKGREEN}Tools:{Colors.ENDC} No tools \n")


    def get_assistant(self, assistant_name):

        for assistant in self.assistants:
            if assistant.name == assistant_name:
                return assistant
        print('No assistant found')
        return None

    def triage_request(self, assistant, message):
        """
        Analyze the user message and delegate it to the appropriate assistant.
        """
        assistant_name = None

        # Determine the appropriate assistant for the message
        if assistant.sub_assistants is not None:
            assistant_name = self.determine_appropriate_assistant(assistant, message)
            if not assistant_name:
                print('No appropriate assistant determined')
                return None

            assistant_new = self.get_assistant(assistant_name)
            if not assistant_new:
                print(f'No assistant found with name: {assistant_name}')
                return None

            assistant.pass_context(assistant_new)
            # Pass along context: if the assistant is a sub-assistant, pass along the context of the parent assistant
        else:
            assistant_new = assistant


        # If it's a new assistant, so a sub assistant
        if assistant_name and assistant_name != assistant.name:
            print(
                f"{Colors.OKGREEN}Selecting sub-assistant:{Colors.ENDC} {Colors.BOLD}{assistant_new.name}{Colors.ENDC}"
            )
            assistant.add_assistant_message(f"Selecting sub-assistant: {assistant_new.name}")
        else:
            print(
                f"{Colors.OKGREEN}Assistant:{Colors.ENDC} {Colors.BOLD}{assistant_new.name}{Colors.ENDC}"
            )
        return assistant_new


    def determine_appropriate_assistant(self, assistant, message):
        triage_message = [{"role": "system", "content": TRIAGE_SYSTEM_PROMPT}]
        triage_message.append(
            {
                "role": "user",
                "content": TRIAGE_MESSAGE_PROMPT.format(
                    message,
                    [(asst.name, asst.tools) for asst in [assistant] + [asst for asst in self.assistants if asst.name in assistant.sub_assistants]]                ),
            }
        )
        response = get_completion(self.client, triage_message)
        return response.content

    def initiate_run(self, task, assistant,test_mode):
        """
        Run the request with the selected assistant and monitor its status.
        """
        run = Run(assistant, task.description, self.client)

        #Update assistant with current task and run
        assistant.current_task_id = task.id
        assistant.runs.append(run)


        #Get planner
        planner = assistant.planner
        plan = run.initiate(planner)
        plan_log = {'step': [], 'step_output': []}
        if not isinstance(plan, list):
            plan_log['step'].append('response')
            plan_log['step'].append(plan)
            assistant.add_assistant_message(f"Response to user: {plan}")
            print(f"{Colors.HEADER}Response:{Colors.ENDC} {plan}")

            #add global context
            self.store_context_globally(assistant)
            return plan_log, plan_log

        original_plan = plan.copy()
        iterations = 0

        while plan and iterations< max_iterations:
            if isinstance(plan,list):
              step = plan.pop(0)
            else:
                return "Error generating plan", "Error generating plan"
            assistant.add_tool_message(step)
            human_input_flag = next((tool.human_input for tool in assistant.tools if tool.function.name == step['tool']), False)
            if step['tool']:
                print(f"{Colors.HEADER}Running Tool:{Colors.ENDC} {step['tool']}")
                if human_input_flag:
                    print(f"\n{Colors.HEADER}Tool {step['tool']} requires human input:{Colors.HEADER}")
                    print(f"{Colors.GREY}Tool arguments:{Colors.ENDC} {step['args']}\n")

                    user_confirmation = input(f"Type 'yes' to execute tool, anything else to skip: ")
                    if user_confirmation.lower() != 'yes':
                        assistant.add_assistant_message(f"Tool {step['tool']} execution skipped by user.")
                        print(f"{Colors.GREY}Skipping tool execution.{Colors.ENDC}")
                        plan_log['step'].append('tool_skipped')
                        plan_log['step_output'].append(f'Tool {step["tool"]} execution skipped by user! Task not completed.')
                        continue
                    assistant.add_assistant_message(f"Tool {step['tool']} execution approved by user.")
            tool_output = self.handle_tool_call(assistant, step, test_mode)
            plan_log['step'].append(step)
            plan_log['step_output'].append(tool_output)

            if task.iterate and not is_dict_empty(plan_log) and plan:
               iterations += 1
               new_task = ITERATE_PROMPT.format(task.description, original_plan, plan_log)
               plan = run.generate_plan(new_task)
            # Store the output for the next iteration

            self.store_context_globally(assistant)

        return original_plan, plan_log

    def handle_tool_call(self,assistant, tool_call, test_mode=False):
        tool_name = tool_call['tool']
        tool_dir = os.path.join(os.getcwd(), 'configs/tools', tool_name)
        handler_path = os.path.join(tool_dir, 'handler.py')

        # Dynamically import the handler function from the handler.py file
        if os.path.isfile(handler_path):
            spec = importlib.util.spec_from_file_location(f"{tool_name}_handler", handler_path)
            tool_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(tool_module)
            tool_handler = getattr(tool_module, tool_name)
            # Call the handler function with arguments
            try:
                tool_response = tool_handler(**tool_call['args'])
            except:
                return 'Failed to execute tool'

            try:
                # assistant.add_assistant_message(tool_response.content)
                return tool_response.content
            except:
                # assistant.add_assistant_message(tool_response)
                return tool_response

        print('No tool file found')
        return 'No tool file found'

    def run_task(self, task, test_mode):
            """
            Processes a given task.
            """

            if not test_mode:
                print(
            f"{Colors.OKCYAN}User Query:{Colors.ENDC} {Colors.BOLD}{task.description}{Colors.ENDC}"
                )
            else:
                print(
            f"{Colors.OKCYAN}Test:{Colors.ENDC} {Colors.BOLD}{task.description}{Colors.ENDC}"
                )
            #Maintain assistant if persist flag is true
            if self.persist and self.last_assistant is not None:
                assistant = self.last_assistant
            else:
                assistant = self.get_assistant(task.assistant)
                assistant.current_task_id = task.id
                assistant.add_user_message(task.description)

            #triage based on current assistant
            selected_assistant = self.triage_request(assistant, task.description)
            if test_mode:
                task.assistant = selected_assistant.name if selected_assistant else "None"
            if not selected_assistant:
                if not test_mode:
                    print(f"No suitable assistant found for the task: {task.description}")
                return None

            # Run the request with the determined or specified assistant
            original_plan, plan_log = self.initiate_run(task, selected_assistant,test_mode)

            #set last assistant
            self.last_assistant = selected_assistant

            #if evaluating the task
            if task.evaluate:
                output = assistant.evaluate(self.client,task, plan_log)
                if output is not None:
                    success_flag = False
                    if not isinstance(output[0],bool):
                     success_flag = False if output[0].lower() == 'false' else bool(output[0])
                    message = output[1]
                    if success_flag:
                        print(f'\n\033[93m{message}\033[0m')
                    else:
                        print(f"{Colors.RED}{message}{Colors.ENDC}")
                    #log
                    assistant.add_assistant_message(message)
                else:
                    message = "Error evaluating output"
                    print(f"{Colors.RED}{message}{Colors.ENDC}")
                    assistant.add_assistant_message(message)

            return original_plan, plan_log


    def run_tests(self):
        total_groundtruth = 0
        total_planning = 0
        total_assistant = 0
        groundtruth_pass = 0
        planning_pass = 0
        assistant_pass = 0
        for task in self.tasks:
            original_plan, plan_log = self.run_task(task, test_mode=True)

            if task.groundtruth:
                total_groundtruth += 1
                # Assuming get_completion returns a response object with a content attribute
                response = get_completion(self.client, [{"role": "user", "content": EVAL_GROUNDTRUTH_PROMPT.format(original_plan, task.groundtruth)}])
                if response.content.lower() == 'true':
                    groundtruth_pass += 1
                    print(f"{Colors.OKGREEN}✔ Groundtruth test passed for: {Colors.ENDC}{task.description}{Colors.OKBLUE}. Expected: {Colors.ENDC}{task.groundtruth}{Colors.OKBLUE}, Got: {Colors.ENDC}{original_plan}{Colors.ENDC}")
                else:
                    print(f"{Colors.RED}✘ Test failed for: {Colors.ENDC}{task.description}{Colors.OKBLUE}. Expected: {Colors.ENDC}{task.groundtruth}{Colors.OKBLUE}, Got: {Colors.ENDC}{original_plan}{Colors.ENDC}")

                total_assistant += 1
                if task.assistant == task.expected_assistant:
                    assistant_pass += 1
                    print(f"{Colors.OKGREEN}✔ Correct assistant assigned. {Colors.ENDC}{Colors.OKBLUE} Expected: {Colors.ENDC}{task.expected_assistant}{Colors.OKBLUE}, Got: {Colors.ENDC}{task.assistant}{Colors.ENDC}\n")
                else:
                    print(f"{Colors.RED}✘ Incorrect assistant assigned. {Colors.ENDC}{Colors.OKBLUE} Expected: {Colors.ENDC}{task.expected_assistant}{Colors.OKBLUE}, Got: {Colors.ENDC}{task.assistant}{Colors.ENDC}\n")


            elif task.expected_plan:
                total_planning += 1
                # Assuming get_completion returns a response object with a content attribute
                response = get_completion(self.client, [{"role": "user", "content": EVAL_PLANNING_PROMPT.format(original_plan, task.expected_plan)}])

                if response.content.lower() == 'true':
                    planning_pass += 1
                    print(f"{Colors.OKGREEN}✔ Planning test passed for: {Colors.ENDC}{task.description}{Colors.OKBLUE}. Expected: {Colors.ENDC}{task.expected_plan}{Colors.OKBLUE}, Got: {Colors.ENDC}{original_plan}{Colors.ENDC}")
                else:
                    print(f"{Colors.RED}✘ Test failed for: {Colors.ENDC}{task.description}{Colors.OKBLUE}. Expected: {Colors.ENDC}{task.expected_plan}{Colors.OKBLUE}, Got: {Colors.ENDC}{original_plan}{Colors.ENDC}")

                total_assistant += 1
                if task.assistant == task.expected_assistant:
                    assistant_pass += 1
                    print(f"{Colors.OKGREEN}✔ Correct assistant assigned.  {Colors.ENDC}{Colors.OKBLUE}Expected: {Colors.ENDC}{task.expected_assistant}{Colors.OKBLUE}, Got: {Colors.ENDC}{task.assistant}{Colors.ENDC}\n")
                else:
                    print(f"{Colors.RED}✘ Incorrect assistant assigned for. {Colors.ENDC}{Colors.OKBLUE} Expected: {Colors.ENDC}{task.expected_assistant}{Colors.OKBLUE}, Got: {Colors.ENDC}{task.assistant}{Colors.ENDC}\n")

            else:
                total_assistant += 1
                if task.assistant == task.expected_assistant:
                    assistant_pass += 1
                    print(f"{Colors.OKGREEN}✔ Correct assistant assigned for: {Colors.ENDC}{task.description}{Colors.OKBLUE}. Expected: {Colors.ENDC}{task.expected_assistant}{Colors.OKBLUE}, Got: {Colors.ENDC}{task.assistant}{Colors.ENDC}\n")
                else:
                    print(f"{Colors.RED}✘ Incorrect assistant assigned for: {Colors.ENDC}{task.description}{Colors.OKBLUE}. Expected: {Colors.ENDC}{task.expected_assistant}{Colors.OKBLUE}, Got: {Colors.ENDC}{task.assistant}{Colors.ENDC}\n")

        if total_groundtruth > 0:
            print(f"\n{Colors.OKGREEN}Passed {groundtruth_pass} groundtruth tests out of {total_groundtruth} tests. Success rate: {groundtruth_pass / total_groundtruth * 100}%{Colors.ENDC}\n")
        if total_planning > 0:
            print(f"{Colors.OKGREEN}Passed {planning_pass} planning tests out of {total_planning} tests. Success rate: {planning_pass / total_planning * 100}%{Colors.ENDC}\n")
        if total_assistant > 0:
            print(f"{Colors.OKGREEN}Passed {assistant_pass} assistant tests out of {total_assistant} tests. Success rate: {assistant_pass / total_assistant * 100}%{Colors.ENDC}\n")
        print("Completed testing the swarm\n\n")

    def deploy(self, client, test_mode=False, test_file_path=None):
        """
        Processes all tasks in the order they are listed in self.tasks.
        """
        self.client = client
        if test_mode and test_file_path:
            print("\nTesting the swarm\n\n")
            self.load_test_tasks(test_file_path)
            self.initialize_and_display_assistants()
            self.run_tests()
            for assistant in self.assistants:
                if assistant.name == 'user_interface':
                    assistant.save_conversation(test=True)
        else:
            print("\n🐝🐝🐝 Deploying the swarm 🐝🐝🐝\n\n")
            self.initialize_and_display_assistants()
            print("\n" + "-" * 100 + "\n")
            for task in self.tasks:
                print('Task',task.id)
                print(f"{Colors.BOLD}Running task{Colors.ENDC}")
                self.run_task(task, test_mode)
                print("\n" + "-" * 100 + "\n")
            #save the session
            for assistant in self.assistants:
                if assistant.name == 'user_interface':
                    assistant.save_conversation()
             #assistant.print_conversation()

    def load_test_tasks(self, test_file_paths):
        self.tasks = []  # Clear any existing tasks
        for f in test_file_paths:
            with open(f, 'r') as file:
                for line in file:
                    test_case = json.loads(line)
                    task = EvaluationTask(description=test_case['text'],
                                assistant=test_case.get('assistant', 'user_interface'),
                                groundtruth=test_case.get('groundtruth',None),
                                expected_plan=test_case.get('expected_plan',None),
                                expected_assistant=test_case['expected_assistant'],
                                iterate=test_case.get('iterate', False),  # Add this
                                evaluate=test_case.get('evaluate', False),
                                eval_function=test_case.get('eval_function', 'default')
                                )
                    self.tasks.append(task)

    def store_context_globally(self, assistant):
        self.global_context['history'].append({assistant.name:assistant.context['history']})

    def initialize_global_history(self):
        self.global_context['history'] = []



---
File: /examples/customer_service_streaming/src/swarm/assistants.py
---

from pydantic import BaseModel
from typing import Any, Optional
from configs.prompts import EVALUATE_TASK_PROMPT
from configs.general import Colors
from src.utils import get_completion
import json
import time


class Assistant(BaseModel):
    log_flag: bool
    name: Optional[str] = None
    instance: Optional[Any] = None
    tools: Optional[list] = None
    current_task_id: str = None
    sub_assistants: Optional[list] = None
    runs: list = []
    context: Optional[dict] = {}
    planner: str = 'sequential' #default to sequential


    def initialize_history(self):
        self.context['history'] = []

    def add_user_message(self, message):
        self.context['history'].append({'task_id':self.current_task_id,'role':'user','content':message})

    def add_assistant_message(self, message):
        self.context['history'].append({'task_id':self.current_task_id,'role':'assistant','content':message})

    def add_tool_message(self, message):
        self.context['history'].append({'task_id':self.current_task_id,'role':'user','tool':message})

    def print_conversation(self):
        print(f"\n{Colors.GREY}Conversation with Assistant: {self.name}{Colors.ENDC}\n")

        # Group messages by run_id
        messages_by_task_id = {}
        for message in self.context['history']:
            task_id = message['task_id']
            if task_id not in messages_by_task_id:
                messages_by_task_id[task_id] = []
            messages_by_task_id[task_id].append(message)

        # Print messages for each run_id
        for task_id, messages in messages_by_task_id.items():
            print(f"{Colors.OKCYAN}Task ID: {task_id}{Colors.ENDC}")
            for message in messages:
                if 'role' in message and message['role'] == 'user':
                    print(f"{Colors.OKBLUE}User:{Colors.ENDC} {message['content']}")
                elif 'tool' in message:
                    tool_message = message['tool']
                    tool_args = ', '.join([f"{arg}: {value}" for arg, value in tool_message['args'].items()])
                    print(f"{Colors.OKGREEN}Tool:{Colors.ENDC} {tool_message['tool']}({tool_args})")
                elif 'role' in message and message['role'] == 'assistant':
                    print(f"{Colors.HEADER}Assistant:{Colors.ENDC} {message['content']}")
            print("\n")

    def evaluate(self, client, task, plan_log):
        '''Evaluates the assistant's performance on a task'''
        output = get_completion(client, [{'role': 'user', 'content': EVALUATE_TASK_PROMPT.format(task.description, plan_log)}])
        output.content = output.content.replace("'",'"')
        try:
            return json.loads(output.content)
        except json.JSONDecodeError:
            print("An error occurred while decoding the JSON.")
            return None

    def save_conversation(self,test=False):
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        if not test:
            filename = f'logs/session_{timestamp}.json'
        else:
            filename = f'tests/test_runs/test_{timestamp}.json'

        with open(filename, 'w') as file:
            json.dump(self.context['history'], file)

    def pass_context(self,assistant):
        '''Passes the context of the conversation to the assistant'''
        assistant.context['history'] = self.context['history']



---
File: /examples/customer_service_streaming/src/swarm/conversation.py
---

class Conversation:
    def __init__(self):
        self.history = []  # Stores all messages, tool calls, and outputs
        self.current_messages = []  # Stores messages of the current interaction
        self.summary = None

    def add_tool_call(self, tool_call):
        self.history.append(tool_call)

    def add_output(self, output):
        self.history.append(output)

    def summarize(self):
        # Implement summarization logic here
        self.summary = "Summary of the conversation"

    def get_summary(self):
        if not self.summary:
            self.summarize()
        return self.summary

    def clear_current_messages(self):
        self.current_messages = []

    def __repr__(self):
        return f"Conversation(History: {len(self.history)}, Current Messages: {len(self.current_messages)}, Summary: {self.summary})"



---
File: /examples/customer_service_streaming/src/swarm/swarm.py
---

import json
from openai import OpenAI
from src.tasks.task import Task, EvaluationTask
from src.swarm.engines.assistants_engine import AssistantsEngine
from src.swarm.engines.local_engine import LocalEngine
from configs.general import Colors, tasks_path

# This class represents the main control unit for deploying and managing tasks within the swarm system.


class Swarm:
    def __init__(self, engine_name, tasks=[], persist=False):
        self.tasks = tasks
        self.engine_name = engine_name
        self.engine = None
        self.persist = persist

    def deploy(self, test_mode=False, test_file_paths=None):
        """
        Processes all tasks in the order they are listed in self.tasks.
        """
        client = OpenAI()
        # Initialize swarm first
        if self.engine_name == 'assistants':
            print(f"{Colors.GREY}Selected engine: Assistants{Colors.ENDC}")
            self.engine = AssistantsEngine(client, self.tasks)
            self.engine.deploy(client, test_mode, test_file_paths)

        elif self.engine_name == 'local':
            print(f"{Colors.GREY}Selected engine: Local{Colors.ENDC}")
            self.engine = LocalEngine(client, self.tasks, persist=self.persist)
            self.engine.deploy(client, test_mode, test_file_paths)

    def load_tasks(self):
        self.tasks = []
        with open(tasks_path, 'r') as file:
            tasks_data = json.load(file)
            for task_json in tasks_data:
                task = Task(description=task_json['description'],
                            iterate=task_json.get('iterate', False),
                            evaluate=task_json.get('evaluate', False),
                            assistant=task_json.get('assistant', 'user_interface'))
                self.tasks.append(task)

    def add_task(self, task):
        self.tasks.append(task)



---
File: /examples/customer_service_streaming/src/swarm/tool.py
---

from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Literal


class Parameter(BaseModel):
    type: str
    description: Optional[str] = None
    enum: Optional[List[str]] = Field(None, alias='choices')


class FunctionParameters(BaseModel):
    type: Literal['object']  # Ensuring it's always 'object'
    properties: Dict[str, Parameter] = {}
    required: Optional[List[str]] = None


class FunctionTool(BaseModel):
    name: str
    description: Optional[str]
    parameters: FunctionParameters


class Tool(BaseModel):
    type: str
    function: Optional[FunctionTool]
    human_input: Optional[bool] = False



---
File: /examples/customer_service_streaming/src/tasks/task.py
---

import uuid

class Task:
    def __init__(self, description, iterate=False, evaluate=False, assistant='user_interface'):
        self.id = str(uuid.uuid4())
        self.description = description
        self.assistant = assistant
        self.iterate: bool = iterate
        self.evaluate: bool = evaluate


class EvaluationTask(Task):
    def __init__(self, description, assistant,iterate, evaluate, groundtruth, expected_assistant, eval_function, expected_plan):
        super().__init__(description=description, assistant=assistant,iterate=iterate, evaluate=evaluate)
        self.groundtruth = groundtruth
        self.expected_assistant = expected_assistant
        self.expected_plan = expected_plan
        self.eval_function = eval_function



---
File: /examples/customer_service_streaming/src/__init__.py
---




---
File: /examples/customer_service_streaming/src/arg_parser.py
---

import argparse

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--engine", choices=["local", "assistants"], default="local", help="Choose the engine to use.")
    parser.add_argument("--test", nargs='*', help="Run the tests.")
    parser.add_argument("--create-task", type=str, help="Create a new task with the given description.")
    parser.add_argument("task_description", type=str, nargs="?", default="", help="Description of the task to create.")
    parser.add_argument("--assistant", type=str, help="Specify the assistant for the new task.")
    parser.add_argument("--evaluate", action="store_true", help="Set the evaluate flag for the new task.")
    parser.add_argument("--iterate", action="store_true", help="Set the iterate flag for the new task.")
    parser.add_argument("--input", action="store_true", help="If we want CLI")

    return parser.parse_args()



---
File: /examples/customer_service_streaming/src/utils.py
---

def get_completion(client,
    messages: list[dict[str, str]],
    model: str = "gpt-4-0125-preview",
    max_tokens=2000,
    temperature=0.7,
    tools=None, 
    stream=False,):

    # Prepare the request parameters
    request_params = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "stream": stream,
    }

    if tools and isinstance(tools, list):
        request_params["tools"] = tools  # Tools are already in dictionary format

    # Make the API call with the possibility of streaming
    if stream:
        completion = client.chat.completions.create(**request_params)
        # create variables to collect the stream of chunks
        collected_chunks = []
        collected_messages = []
        for chunk in completion:
            collected_chunks.append(chunk)  # save the event response
            chunk_message = chunk.choices[0].delta.content  # extract the message
            collected_messages.append(chunk_message)  # save the message
            print(chunk_message, end="")  # print the message
            # yield chunk_message  # Yield each part of the completion as it arrives
        return collected_messages  # Returns the whole completion 
    else:
        completion = client.chat.completions.create(**request_params)
        return completion.choices[0].message  # Returns the whole completion 


def is_dict_empty(d):
    return all(not v for v in d.values())



---
File: /examples/customer_service_streaming/src/validator.py
---

import os
import importlib
import json
from src.swarm.tool import Tool
from src.swarm.assistants import Assistant

def validate_tool(tool_definition):
    # Validate the tool using its schema
    Tool(**tool_definition)  # Uncomment if you have a schema to validate tools
    print(f"Validating tool: {tool_definition['function']['name']}")

def validate_all_tools(engine):
    tools_path = os.path.join(os.getcwd(), 'configs/tools')
    for tool_dir in os.listdir(tools_path):
        if '__pycache__' in tool_dir:
            continue
        tool_dir_path = os.path.join(tools_path, tool_dir)
        if os.path.isdir(tool_dir_path):
            # Validate tool.json
            tool_json_path = os.path.join(tool_dir_path, 'tool.json')
            handler_path = os.path.join(tool_dir_path, 'handler.py')
            if os.path.isfile(tool_json_path) and os.path.isfile(handler_path):
                with open(tool_json_path, 'r') as file:
                    tool_def = json.load(file)
                    tool_name_from_json = tool_def['function']['name']

                    # Check if the folder name matches the tool name in tool.json
                    if tool_name_from_json != tool_dir:
                        print(f"Mismatch in tool folder name and tool name in JSON for {tool_dir}")
                    else:
                        print(f"{tool_dir}/tool.json tool name matches folder name.")

                    # Check if the function name in handler.py matches the tool name
                    spec = importlib.util.spec_from_file_location(f"{tool_dir}_handler", handler_path)
                    tool_module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(tool_module)

                    # Verify if the function exists in handler.py and matches the name
                    if hasattr(tool_module, tool_dir):
                        print(f"{tool_dir}/handler.py contains a matching function name.")
                    else:
                        print(f"{tool_dir}/handler.py does not contain a function '{tool_dir}'.")

            else:
                if not os.path.isfile(tool_json_path):
                    print(f"Missing tool.json in {tool_dir} tool folder.")
                if not os.path.isfile(handler_path):
                    print(f"Missing handler.py in {tool_dir} tool folder.")
    print('\n')

    # Function to validate all assistants
def validate_all_assistants():
    assistants_path = os.path.join(os.getcwd(), 'configs/assistants')
    for root, dirs, files in os.walk(assistants_path):
        for file in files:
            if file.endswith('assistant.json'):
                file_path = os.path.join(root, file)
                with open(file_path, 'r') as file:
                        assistant_data = json.load(file)[0]  # Access the first dictionary in the list
                        try:
                            Assistant(**assistant_data)
                            print(f"{os.path.basename(root)} assistant validated!")
                        except:
                            Assistant(**assistant_data)
                            print(f"Assistant validation failed!")
    print('\n')



---
File: /examples/customer_service_streaming/tests/test_runs/.gitkeep
---




---
File: /examples/customer_service_streaming/tests/test_prompts.jsonl
---

{"text": "Explain the DALL-E editor interface?", "expected_assistant": "user_interface"}
{"text": "How does the OpenAI moderation API work?", "expected_assistant": "user_interface"}
{"text": "How many slices of pizza would everyone get if you split 12 slices equally among 3 people","groundtruth": "4", "expected_assistant": "user_interface"}
{"text": "Are users allowed to change DALL-E email from what they signed up with?", "expected_plan":[{"tool": "query_docs", "args": {"query": "Are users allowed to change DALL-E email from what they signed up with?"}}], "expected_assistant": "user_interface"}



---
File: /examples/customer_service_streaming/.gitignore
---

**/src/threads/thread_data.json
**/__pycache__/**
**/threads/thread_data.json
**/logs/session_*
**/test_runs/test_*



---
File: /examples/customer_service_streaming/docker-compose.yaml
---

version: '3.4'
services:
  qdrant:
    image: qdrant/qdrant:v1.3.0
    restart: on-failure
    ports:
      - "6333:6333"
      - "6334:6334"



---
File: /examples/customer_service_streaming/main.py
---

import shlex
import argparse
from src.swarm.swarm import Swarm
from src.tasks.task import Task
from configs.general import test_root, test_file, engine_name, persist
from src.validator import validate_all_tools, validate_all_assistants
from src.arg_parser import parse_args


def main():
    args = parse_args()
    try:
        validate_all_tools(engine_name)
        validate_all_assistants()
    except:
        raise Exception("Validation failed")

    swarm = Swarm(
        engine_name=engine_name, persist=persist)

    if args.test is not None:
        test_files = args.test
        if len(test_files) == 0:
            test_file_paths = [f"{test_root}/{test_file}"]
        else:
            test_file_paths = [f"{test_root}/{file}" for file in test_files]
        swarm = Swarm(engine_name='local')
        swarm.deploy(test_mode=True, test_file_paths=test_file_paths)

    elif args.input:
        # Interactive mode for adding tasks
        while True:
            print("Enter a task (or 'exit' to quit):")
            task_input = input()

            # Check for exit command
            if task_input.lower() == 'exit':
                break

            # Use shlex to parse the task description and arguments
            task_args = shlex.split(task_input)
            task_parser = argparse.ArgumentParser()
            task_parser.add_argument("description", type=str, nargs='?', default="")
            task_parser.add_argument("--iterate", action="store_true", help="Set the iterate flag for the new task.")
            task_parser.add_argument("--evaluate", action="store_true", help="Set the evaluate flag for the new task.")
            task_parser.add_argument("--assistant", type=str, default="user_interface", help="Specify the assistant for the new task.")

            # Parse task arguments
            task_parsed_args = task_parser.parse_args(task_args)

            # Create and add the new task
            new_task = Task(description=task_parsed_args.description,
                            iterate=task_parsed_args.iterate,
                            evaluate=task_parsed_args.evaluate,
                            assistant=task_parsed_args.assistant)
            swarm.add_task(new_task)

            # Deploy Swarm with the new task
            swarm.deploy()
            swarm.tasks.clear()

    else:
        # Load predefined tasks if any
        # Deploy the Swarm for predefined tasks
        swarm.load_tasks()
        swarm.deploy()

    print("\n\n🍯🐝🍯 Swarm operations complete 🍯🐝🍯\n\n")


if __name__ == "__main__":
    main()



---
File: /examples/customer_service_streaming/prep_data.py
---

import os
import json
from openai import OpenAI

client = OpenAI()
GPT_MODEL = 'gpt-4'
EMBEDDING_MODEL = "text-embedding-3-large"

article_list = os.listdir('data')

articles = []

for x in article_list:

    article_path = 'data/' + x

    # Opening JSON file
    f = open(article_path)

    # returns JSON object as
    # a dictionary
    data = json.load(f)

    articles.append(data)

    # Closing file
    f.close()

for i, x in enumerate(articles):
    try:
        embedding = client.embeddings.create(model=EMBEDDING_MODEL,input=x['text'])
        articles[i].update({"embedding": embedding.data[0].embedding})
    except Exception as e:
        print(x['title'])
        print(e)

import qdrant_client
from qdrant_client.http import models as rest
import pandas as pd


qdrant = qdrant_client.QdrantClient(host='localhost')
qdrant.get_collections()

collection_name = 'help_center'

vector_size = len(articles[0]['embedding'])
vector_size

article_df = pd.DataFrame(articles)
article_df.head()

# Create Vector DB collection
qdrant.recreate_collection(
    collection_name=collection_name,
    vectors_config={
        'article': rest.VectorParams(
            distance=rest.Distance.COSINE,
            size=vector_size,
        )
    }
)

# Populate collection with vectors

qdrant.upsert(
    collection_name=collection_name,
    points=[
        rest.PointStruct(
            id=k,
            vector={
                'article': v['embedding'],
            },
            payload=v.to_dict(),
        )
        for k, v in article_df.iterrows()
    ],
)



---
File: /examples/support_bot/data/article_6233728.json
---

{"text": "Introduction\n============\n\n\n\u200bSince releasing the Answers endpoint in beta last year, we\u2019ve developed new methods that achieve better results for this task. As a result, we\u2019ll be removing the Answers endpoint from our documentation and removing access to this endpoint on December 3, 2022 for all organizations. New accounts created after June 3rd will not have access to this endpoint.\n\n\n\nWe strongly encourage developers to switch over to newer techniques which produce better results, outlined below.\n\n\n\nCurrent documentation\n---------------------\n\n\n<https://beta.openai.com/docs/guides/answers> \n\n\n<https://beta.openai.com/docs/api-reference/answers>\n\n\n\nOptions\n=======\n\n\nAs a quick review, here are the high level steps of the current Answers endpoint:\n\n\n\n\n![](https://openai.intercom-attachments-7.com/i/o/524217540/51eda23e171f33f1b9d5acff/rM6ZVI3XZ2CpxcEStmG5mFy6ATBCskmX2g3_GPmeY3FicvrWfJCuFOtzsnbkpMQe-TQ6hi5j1BV9cFo7bCDcsz8VWxFfeOnC1Gb4QNaeVYtJq4Qtg76SBOLLk-jgHUA8mWZ0QgOuV636UgcvMA)All of these options are also outlined [here](https://github.com/openai/openai-cookbook/tree/main/transition_guides_for_deprecated_API_endpoints)\n\n\n\nOption 1: Transition to Embeddings-based search (recommended)\n-------------------------------------------------------------\n\n\nWe believe that most use cases will be better served by moving the underlying search system to use a vector-based embedding search. The major reason for this is that our current system used a bigram filter to narrow down the scope of candidates whereas our embeddings system has much more contextual awareness. Also, in general, using embeddings will be considerably lower cost in the long run. If you\u2019re not familiar with this, you can learn more by visiting our [guide to embeddings](https://beta.openai.com/docs/guides/embeddings/use-cases).\n\n\n\nIf you\u2019re using a small dataset (<10,000 documents), consider using the techniques described in that guide to find the best documents to construct a prompt similar to [this](#h_89196129b2). Then, you can just submit that prompt to our [Completions](https://beta.openai.com/docs/api-reference/completions) endpoint.\n\n\n\nIf you have a larger dataset, consider using a vector search engine like [Pinecone](https://share.streamlit.io/pinecone-io/playground/beyond_search_openai/src/server.py) or [Weaviate](https://weaviate.io/developers/weaviate/current/retriever-vectorizer-modules/text2vec-openai.html) to power that search.\n\n\n\nOption 2: Reimplement existing functionality\n--------------------------------------------\n\n\nIf you\u2019d like to recreate the functionality of the Answers endpoint, here\u2019s how we did it. There is also a [script](https://github.com/openai/openai-cookbook/blob/main/transition_guides_for_deprecated_API_endpoints/answers_functionality_example.py) that replicates most of this functionality.\n\n\n\nAt a high level, there are two main ways you can use the answers endpoint: you can source the data from an uploaded file or send it in with the request.\n\n\n\n**If you\u2019re using the document parameter**\n------------------------------------------\n\n\nThere\u2019s only one step if you provide the documents in the Answers API call.\n\n\n\nHere\u2019s roughly the steps we used: \n\n\n* Construct the prompt [with this format.](#h_89196129b2)\n* Gather all of the provided documents. If they fit in the prompt, just use all of them.\n* Do an [OpenAI search](https://beta.openai.com/docs/api-reference/searches) (note that this is also being deprecated and has a [transition guide](https://app.intercom.com/a/apps/dgkjq2bp/articles/articles/6272952/show)) where the documents are the user provided documents and the query is the query from above. Rank the documents by score.\n* In order of score, attempt to add Elastic search documents until you run out of space in the context.\n* Request a completion with the provided parameters (logit\\_bias, n, stop, etc)\n\n\nThroughout all of this, you\u2019ll need to check that the prompt\u2019s length doesn\u2019t exceed [the model's token limit](https://beta.openai.com/docs/engines/gpt-3). To assess the number of tokens present in a prompt, we recommend <https://huggingface.co/docs/transformers/model_doc/gpt2#transformers.GPT2TokenizerFast>. \n\n\n\nIf you're using the file parameter\n----------------------------------\n\n\nStep 1: upload a jsonl file\n\n\n\nBehind the scenes, we upload new files meant for answers to an Elastic search cluster. Each line of the jsonl is then submitted as a document.\n\n\n\nIf you uploaded the file with the purpose \u201canswers,\u201d we additionally split the documents on newlines and upload each of those chunks as separate documents to ensure that we can search across and reference the highest number of relevant text sections in the file.\n\n\n\nEach line requires a \u201ctext\u201d field and an optional \u201cmetadata\u201d field.\n\n\n\nThese are the Elastic search settings and mappings for our index:\n\n\n\n[Elastic searching mapping](https://www.elastic.co/guide/en/elasticsearch/reference/current/mapping.html): \n\n\n\n```\n{  \n    \"properties\": {  \n        \"document\": {\"type\": \"text\", \"analyzer\": \"standard_bigram_analyzer\"}, -> the \u201ctext\u201d field  \n        \"metadata\": {\"type\": \"object\", \"enabled\": False}, -> the \u201cmetadata\u201d field  \n    }  \n}\n```\n\n\n[Elastic search analyzer](https://www.elastic.co/guide/en/elasticsearch/reference/current/mapping.html):\n\n\n\n```\n{  \n    \"analysis\": {  \n        \"analyzer\": {  \n            \"standard_bigram_analyzer\": {  \n                \"type\": \"custom\",  \n                \"tokenizer\": \"standard\",  \n                \"filter\": [\"lowercase\", \"english_stop\", \"shingle\"],  \n            }  \n        },  \n        \"filter\": {\"english_stop\": {\"type\": \"stop\", \"stopwords\": \"_english_\"}},  \n    }  \n}\n```\n\n\nAfter that, we performed [standard Elastic search search calls](https://elasticsearch-py.readthedocs.io/en/v8.2.0/api.html#elasticsearch.Elasticsearch.search) and used `max\\_rerank` to determine the number of documents to return from Elastic search.\n\n\n\nStep 2: Search\n\n\nHere\u2019s roughly the steps we used. Our end goal is to create a [Completions](https://beta.openai.com/docs/api-reference/completions) request [with this format](#h_89196129b2). It will look very similar to [Documents](#h_cb1d8a8d3f)\n\n\n\nFrom there, our steps are: \n\n\n* Start with the `experimental\\_alternative\\_question` or, if that's not provided, what\u2019s in the `question` field. Call that the query.\n* Query Elastic search for `max\\_rerank` documents with query as the search param.\n* Take those documents and do an [OpenAI search](https://beta.openai.com/docs/api-reference/searches) on them where the entries from Elastic search are the docs, and the query is the query that you used above. Use the score from the search to rank the documents.\n* In order of score, attempt to add Elastic search documents until you run out of space in the prompt.\n* Request an OpenAI completion with the provided parameters (logit\\_bias, n, stop, etc). Return that answer to the user.\n\n\nCompletion Prompt\n-----------------\n\n\n\n```\n===  \nContext: #{{ provided examples_context }}  \n===  \nQ: example 1 question  \nA: example 1 answer  \n---  \nQ: example 2 question  \nA: example 2 answer  \n(and so on for all examples provided in the request)   \n===  \nContext: #{{ what we return from Elasticsearch }}  \n===  \nQ: #{{ user provided question }}   \nA:\n```\n", "title": "Answers Transition Guide", "article_id": "6233728", "url": "https://help.openai.com/en/articles/6233728-answers-transition-guide"}


---
File: /examples/support_bot/__init__.py
---




---
File: /examples/support_bot/customer_service.py
---

import re

import qdrant_client
from openai import OpenAI

from swarm import Agent
from swarm.repl import run_demo_loop

# Initialize connections
client = OpenAI()
qdrant = qdrant_client.QdrantClient(host="localhost")

# Set embedding model
EMBEDDING_MODEL = "text-embedding-3-large"

# Set qdrant collection
collection_name = "help_center"


# TODO: Make this work


def query_qdrant(query, collection_name, vector_name="article", top_k=5):
    # Creates embedding vector from user query
    embedded_query = (
        client.embeddings.create(
            input=query,
            model=EMBEDDING_MODEL,
        )
        .data[0]
        .embedding
    )

    query_results = qdrant.search(
        collection_name=collection_name,
        query_vector=(vector_name, embedded_query),
        limit=top_k,
    )

    return query_results


def query_docs(query):
    print(f"Searching knowledge base with query: {query}")
    query_results = query_qdrant(query, collection_name=collection_name)
    output = []

    for i, article in enumerate(query_results):
        title = article.payload["title"]
        text = article.payload["text"]
        url = article.payload["url"]

        output.append((title, text, url))

    if output:
        title, content, _ = output[0]
        response = f"Title: {title}\nContent: {content}"
        truncated_content = re.sub(
            r"\s+", " ", content[:50] + "..." if len(content) > 50 else content
        )
        print("Most relevant article title:", truncated_content)
        return {"response": response}
    else:
        print("No results")
        return {"response": "No results found."}


def send_email(email_address, message):
    response = f"Email sent to: {email_address} with message: {message}"
    return {"response": response}


def submit_ticket(description):
    return {"response": f"Ticket created for {description}"}


user_interface_agent = Agent(
    name="User Interface Agent",
    instructions="You are a user interface agent that handles all interactions with the user. Call this agent for general questions and when no other agent is correct for the user query.",
    functions=[query_docs, submit_ticket, send_email],
)

help_center_agent = Agent(
    name="Help Center Agent",
    instructions="You are an OpenAI help center agent who deals with questions about OpenAI products, such as GPT models, DALL-E, Whisper, etc.",
    functions=[query_docs, submit_ticket, send_email],
)


def transfer_to_help_center():
    """Transfer the user to the help center agent."""
    return help_center_agent


user_interface_agent.functions.append(transfer_to_help_center)

if __name__ == "__main__":
    run_demo_loop(user_interface_agent)



---
File: /examples/support_bot/docker-compose.yaml
---

version: '3.4'
services:
  qdrant:
    image: qdrant/qdrant:v1.3.0
    restart: on-failure
    ports:
      - "6335:6335"



---
File: /examples/support_bot/main.py
---

import re

import qdrant_client
from openai import OpenAI

from swarm import Agent
from swarm.repl import run_demo_loop

# Initialize connections
client = OpenAI()
qdrant = qdrant_client.QdrantClient(host="localhost")

# Set embedding model
EMBEDDING_MODEL = "text-embedding-3-large"

# Set qdrant collection
collection_name = "help_center"


def query_qdrant(query, collection_name, vector_name="article", top_k=5):
    # Creates embedding vector from user query
    embedded_query = (
        client.embeddings.create(
            input=query,
            model=EMBEDDING_MODEL,
        )
        .data[0]
        .embedding
    )

    query_results = qdrant.search(
        collection_name=collection_name,
        query_vector=(vector_name, embedded_query),
        limit=top_k,
    )

    return query_results


def query_docs(query):
    """Query the knowledge base for relevant articles."""
    print(f"Searching knowledge base with query: {query}")
    query_results = query_qdrant(query, collection_name=collection_name)
    output = []

    for i, article in enumerate(query_results):
        title = article.payload["title"]
        text = article.payload["text"]
        url = article.payload["url"]

        output.append((title, text, url))

    if output:
        title, content, _ = output[0]
        response = f"Title: {title}\nContent: {content}"
        truncated_content = re.sub(
            r"\s+", " ", content[:50] + "..." if len(content) > 50 else content
        )
        print("Most relevant article title:", truncated_content)
        return {"response": response}
    else:
        print("No results")
        return {"response": "No results found."}


def send_email(email_address, message):
    """Send an email to the user."""
    response = f"Email sent to: {email_address} with message: {message}"
    return {"response": response}


def submit_ticket(description):
    """Submit a ticket for the user."""
    return {"response": f"Ticket created for {description}"}


def transfer_to_help_center():
    """Transfer the user to the help center agent."""
    return help_center_agent


user_interface_agent = Agent(
    name="User Interface Agent",
    instructions="You are a user interface agent that handles all interactions with the user. Call this agent for general questions and when no other agent is correct for the user query.",
    functions=[transfer_to_help_center],
)

help_center_agent = Agent(
    name="Help Center Agent",
    instructions="You are an OpenAI help center agent who deals with questions about OpenAI products, such as GPT models, DALL-E, Whisper, etc.",
    functions=[query_docs, submit_ticket, send_email],
)

if __name__ == "__main__":
    run_demo_loop(user_interface_agent)



---
File: /examples/support_bot/Makefile
---

install:
	 pip3 install -r requirements.txt
prep:
	 python3 prep_data.py
run:
	 PYTHONPATH=../.. python3 -m main


---
File: /examples/support_bot/prep_data.py
---

import json
import os

import pandas as pd
import qdrant_client
from openai import OpenAI
from qdrant_client.http import models as rest

client = OpenAI()
GPT_MODEL = "gpt-4o"
EMBEDDING_MODEL = "text-embedding-3-large"

article_list = os.listdir("data")

articles = []

for x in article_list:
    article_path = "data/" + x

    # Opening JSON file
    f = open(article_path)

    # returns JSON object as
    # a dictionary
    data = json.load(f)

    articles.append(data)

    # Closing file
    f.close()

for i, x in enumerate(articles):
    try:
        embedding = client.embeddings.create(model=EMBEDDING_MODEL, input=x["text"])
        articles[i].update({"embedding": embedding.data[0].embedding})
    except Exception as e:
        print(x["title"])
        print(e)

qdrant = qdrant_client.QdrantClient(host="localhost")
qdrant.get_collections()

collection_name = "help_center"

vector_size = len(articles[0]["embedding"])
vector_size

article_df = pd.DataFrame(articles)
article_df.head()

# Delete the collection if it exists, so we can rewrite it changes to articles were made
if qdrant.get_collection(collection_name=collection_name):
    qdrant.delete_collection(collection_name=collection_name)

# Create Vector DB collection
qdrant.create_collection(
    collection_name=collection_name,
    vectors_config={
        "article": rest.VectorParams(
            distance=rest.Distance.COSINE,
            size=vector_size,
        )
    },
)

# Populate collection with vectors

qdrant.upsert(
    collection_name=collection_name,
    points=[
        rest.PointStruct(
            id=k,
            vector={
                "article": v["embedding"],
            },
            payload=v.to_dict(),
        )
        for k, v in article_df.iterrows()
    ],
)



---
File: /examples/support_bot/README.md
---

# Support bot

This example is a customer service bot which includes a user interface agent and a help center agent with several tools.
This example uses the helper function `run_demo_loop`, which allows us to create an interactive Swarm session.

## Overview

The support bot consists of two main agents:

1. **User Interface Agent**: Handles initial user interactions and directs them to the help center agent based on their needs.
2. **Help Center Agent**: Provides detailed help and support using various tools and integrated with a Qdrant VectorDB for documentation retrieval.

## Setup

To start the support bot:

1. Ensure Docker is installed and running on your system.
2. Install the necessary additional libraries:

```shell
make install
```

3. Initialize docker

```shell
docker-compose up -d
```

4. Prepare the vector DB:

```shell
make prep
```

5. Run the main scripy:

```shell
make run
```



---
File: /examples/support_bot/requirements.txt
---

qdrant-client


---
File: /examples/triage_agent/agents.py
---

from swarm import Agent


def process_refund(item_id, reason="NOT SPECIFIED"):
    """Refund an item. Refund an item. Make sure you have the item_id of the form item_... Ask for user confirmation before processing the refund."""
    print(f"[mock] Refunding item {item_id} because {reason}...")
    return "Success!"


def apply_discount():
    """Apply a discount to the user's cart."""
    print("[mock] Applying discount...")
    return "Applied discount of 11%"


triage_agent = Agent(
    name="Triage Agent",
    instructions="Determine which agent is best suited to handle the user's request, and transfer the conversation to that agent.",
)
sales_agent = Agent(
    name="Sales Agent",
    instructions="Be super enthusiastic about selling bees.",
)
refunds_agent = Agent(
    name="Refunds Agent",
    instructions="Help the user with a refund. If the reason is that it was too expensive, offer the user a refund code. If they insist, then process the refund.",
    functions=[process_refund, apply_discount],
)


def transfer_back_to_triage():
    """Call this function if a user is asking about a topic that is not handled by the current agent."""
    return triage_agent


def transfer_to_sales():
    return sales_agent


def transfer_to_refunds():
    return refunds_agent


triage_agent.functions = [transfer_to_sales, transfer_to_refunds]
sales_agent.functions.append(transfer_back_to_triage)
refunds_agent.functions.append(transfer_back_to_triage)



---
File: /examples/triage_agent/evals_util.py
---

from openai import OpenAI
import instructor
from pydantic import BaseModel
from typing import Optional

__client = instructor.from_openai(OpenAI())


class BoolEvalResult(BaseModel):
    value: bool
    reason: Optional[str]


def evaluate_with_llm_bool(instruction, data) -> BoolEvalResult:
    eval_result, _ = __client.chat.completions.create_with_completion(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": instruction},
            {"role": "user", "content": data},
        ],
        response_model=BoolEvalResult,
    )
    return eval_result



---
File: /examples/triage_agent/evals.py
---

from swarm import Swarm
from agents import triage_agent, sales_agent, refunds_agent
from evals_util import evaluate_with_llm_bool, BoolEvalResult
import pytest
import json

client = Swarm()

CONVERSATIONAL_EVAL_SYSTEM_PROMPT = """
You will be provided with a conversation between a user and an agent, as well as a main goal for the conversation.
Your goal is to evaluate, based on the conversation, if the agent achieves the main goal or not.

To assess whether the agent manages to achieve the main goal, consider the instructions present in the main goal, as well as the way the user responds:
is the answer satisfactory for the user or not, could the agent have done better considering the main goal?
It is possible that the user is not satisfied with the answer, but the agent still achieves the main goal because it is following the instructions provided as part of the main goal.
"""


def conversation_was_successful(messages) -> bool:
    conversation = f"CONVERSATION: {json.dumps(messages)}"
    result: BoolEvalResult = evaluate_with_llm_bool(
        CONVERSATIONAL_EVAL_SYSTEM_PROMPT, conversation
    )
    return result.value


def run_and_get_tool_calls(agent, query):
    message = {"role": "user", "content": query}
    response = client.run(
        agent=agent,
        messages=[message],
        execute_tools=False,
    )
    return response.messages[-1].get("tool_calls")


@pytest.mark.parametrize(
    "query,function_name",
    [
        ("I want to make a refund!", "transfer_to_refunds"),
        ("I want to talk to sales.", "transfer_to_sales"),
    ],
)
def test_triage_agent_calls_correct_function(query, function_name):
    tool_calls = run_and_get_tool_calls(triage_agent, query)

    assert len(tool_calls) == 1
    assert tool_calls[0]["function"]["name"] == function_name


@pytest.mark.parametrize(
    "messages",
    [
        [
            {"role": "user", "content": "Who is the lead singer of U2"},
            {"role": "assistant", "content": "Bono is the lead singer of U2."},
        ],
        [
            {"role": "user", "content": "Hello!"},
            {"role": "assistant", "content": "Hi there! How can I assist you today?"},
            {"role": "user", "content": "I want to make a refund."},
            {"role": "tool", "tool_name": "transfer_to_refunds"},
            {"role": "user", "content": "Thank you!"},
            {"role": "assistant", "content": "You're welcome! Have a great day!"},
        ],
    ],
)
def test_conversation_is_successful(messages):
    result = conversation_was_successful(messages)
    assert result == True



---
File: /examples/triage_agent/run.py
---

from swarm.repl import run_demo_loop
from agents import triage_agent

if __name__ == "__main__":
    run_demo_loop(triage_agent)



---
File: /examples/weather_agent/agents.py
---

import json

from swarm import Agent


def get_weather(location, time="now"):
    """Get the current weather in a given location. Location MUST be a city."""
    return json.dumps({"location": location, "temperature": "65", "time": time})


def send_email(recipient, subject, body):
    print("Sending email...")
    print(f"To: {recipient}")
    print(f"Subject: {subject}")
    print(f"Body: {body}")
    return "Sent!"


weather_agent = Agent(
    name="Weather Agent",
    instructions="You are a helpful agent.",
    functions=[get_weather, send_email],
)



---
File: /examples/weather_agent/evals.py
---

from swarm import Swarm
from agents import weather_agent
import pytest

client = Swarm()


def run_and_get_tool_calls(agent, query):
    message = {"role": "user", "content": query}
    response = client.run(
        agent=agent,
        messages=[message],
        execute_tools=False,
    )
    return response.messages[-1].get("tool_calls")


@pytest.mark.parametrize(
    "query",
    [
        "What's the weather in NYC?",
        "Tell me the weather in London.",
        "Do I need an umbrella today? I'm in chicago.",
    ],
)
def test_calls_weather_when_asked(query):
    tool_calls = run_and_get_tool_calls(weather_agent, query)

    assert len(tool_calls) == 1
    assert tool_calls[0]["function"]["name"] == "get_weather"


@pytest.mark.parametrize(
    "query",
    [
        "Who's the president of the United States?",
        "What is the time right now?",
        "Hi!",
    ],
)
def test_does_not_call_weather_when_not_asked(query):
    tool_calls = run_and_get_tool_calls(weather_agent, query)

    assert not tool_calls



---
File: /examples/weather_agent/run.py
---

from swarm.repl import run_demo_loop
from agents import weather_agent

if __name__ == "__main__":
    run_demo_loop(weather_agent, stream=True)



---
File: /examples/__init__.py
---




---
File: /swarm/repl/__init__.py
---

from .repl import run_demo_loop



---
File: /swarm/repl/repl.py
---

import json

from swarm import Swarm


def process_and_print_streaming_response(response):
    content = ""
    last_sender = ""

    for chunk in response:
        if "sender" in chunk:
            last_sender = chunk["sender"]

        if "content" in chunk and chunk["content"] is not None:
            if not content and last_sender:
                print(f"\033[94m{last_sender}:\033[0m", end=" ", flush=True)
                last_sender = ""
            print(chunk["content"], end="", flush=True)
            content += chunk["content"]

        if "tool_calls" in chunk and chunk["tool_calls"] is not None:
            for tool_call in chunk["tool_calls"]:
                f = tool_call["function"]
                name = f["name"]
                if not name:
                    continue
                print(f"\033[94m{last_sender}: \033[95m{name}\033[0m()")

        if "delim" in chunk and chunk["delim"] == "end" and content:
            print()  # End of response message
            content = ""

        if "response" in chunk:
            return chunk["response"]


def pretty_print_messages(messages) -> None:
    for message in messages:
        if message["role"] != "assistant":
            continue

        # print agent name in blue
        print(f"\033[94m{message['sender']}\033[0m:", end=" ")

        # print response, if any
        if message["content"]:
            print(message["content"])

        # print tool calls in purple, if any
        tool_calls = message.get("tool_calls") or []
        if len(tool_calls) > 1:
            print()
        for tool_call in tool_calls:
            f = tool_call["function"]
            name, args = f["name"], f["arguments"]
            arg_str = json.dumps(json.loads(args)).replace(":", "=")
            print(f"\033[95m{name}\033[0m({arg_str[1:-1]})")


def run_demo_loop(
    starting_agent, context_variables=None, stream=False, debug=False
) -> None:
    client = Swarm()
    print("Starting Swarm CLI 🐝")

    messages = []
    agent = starting_agent

    while True:
        user_input = input("\033[90mUser\033[0m: ")
        messages.append({"role": "user", "content": user_input})

        response = client.run(
            agent=agent,
            messages=messages,
            context_variables=context_variables or {},
            stream=stream,
            debug=debug,
        )

        if stream:
            response = process_and_print_streaming_response(response)
        else:
            pretty_print_messages(response.messages)

        messages.extend(response.messages)
        agent = response.agent



---
File: /swarm/__init__.py
---

from .core import Swarm
from .types import Agent, Response

__all__ = ["Swarm", "Agent", "Response"]



---
File: /swarm/core.py
---

# Standard library imports
import copy
import json
from collections import defaultdict
from typing import List, Callable, Union

# Package/library imports
from openai import OpenAI


# Local imports
from .util import function_to_json, debug_print, merge_chunk
from .types import (
    Agent,
    AgentFunction,
    ChatCompletionMessage,
    ChatCompletionMessageToolCall,
    Function,
    Response,
    Result,
)

__CTX_VARS_NAME__ = "context_variables"


class Swarm:
    def __init__(self, client=None):
        if not client:
            client = OpenAI()
        self.client = client

    def get_chat_completion(
        self,
        agent: Agent,
        history: List,
        context_variables: dict,
        model_override: str,
        stream: bool,
        debug: bool,
    ) -> ChatCompletionMessage:
        context_variables = defaultdict(str, context_variables)
        instructions = (
            agent.instructions(context_variables)
            if callable(agent.instructions)
            else agent.instructions
        )
        messages = [{"role": "system", "content": instructions}] + history
        debug_print(debug, "Getting chat completion for...:", messages)

        tools = [function_to_json(f) for f in agent.functions]
        # hide context_variables from model
        for tool in tools:
            params = tool["function"]["parameters"]
            params["properties"].pop(__CTX_VARS_NAME__, None)
            if __CTX_VARS_NAME__ in params["required"]:
                params["required"].remove(__CTX_VARS_NAME__)

        create_params = {
            "model": model_override or agent.model,
            "messages": messages,
            "tools": tools or None,
            "tool_choice": agent.tool_choice,
            "stream": stream,
        }

        if tools:
            create_params["parallel_tool_calls"] = agent.parallel_tool_calls

        return self.client.chat.completions.create(**create_params)

    def handle_function_result(self, result, debug) -> Result:
        match result:
            case Result() as result:
                return result

            case Agent() as agent:
                return Result(
                    value=json.dumps({"assistant": agent.name}),
                    agent=agent,
                )
            case _:
                try:
                    return Result(value=str(result))
                except Exception as e:
                    error_message = f"Failed to cast response to string: {result}. Make sure agent functions return a string or Result object. Error: {str(e)}"
                    debug_print(debug, error_message)
                    raise TypeError(error_message)

    def handle_tool_calls(
        self,
        tool_calls: List[ChatCompletionMessageToolCall],
        functions: List[AgentFunction],
        context_variables: dict,
        debug: bool,
    ) -> Response:
        function_map = {f.__name__: f for f in functions}
        partial_response = Response(
            messages=[], agent=None, context_variables={})

        for tool_call in tool_calls:
            name = tool_call.function.name
            # handle missing tool case, skip to next tool
            if name not in function_map:
                debug_print(debug, f"Tool {name} not found in function map.")
                partial_response.messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "tool_name": name,
                        "content": f"Error: Tool {name} not found.",
                    }
                )
                continue
            args = json.loads(tool_call.function.arguments)
            debug_print(
                debug, f"Processing tool call: {name} with arguments {args}")

            func = function_map[name]
            # pass context_variables to agent functions
            if __CTX_VARS_NAME__ in func.__code__.co_varnames:
                args[__CTX_VARS_NAME__] = context_variables
            raw_result = function_map[name](**args)

            result: Result = self.handle_function_result(raw_result, debug)
            partial_response.messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "tool_name": name,
                    "content": result.value,
                }
            )
            partial_response.context_variables.update(result.context_variables)
            if result.agent:
                partial_response.agent = result.agent

        return partial_response

    def run_and_stream(
        self,
        agent: Agent,
        messages: List,
        context_variables: dict = {},
        model_override: str = None,
        debug: bool = False,
        max_turns: int = float("inf"),
        execute_tools: bool = True,
    ):
        active_agent = agent
        context_variables = copy.deepcopy(context_variables)
        history = copy.deepcopy(messages)
        init_len = len(messages)

        while len(history) - init_len < max_turns:

            message = {
                "content": "",
                "sender": agent.name,
                "role": "assistant",
                "function_call": None,
                "tool_calls": defaultdict(
                    lambda: {
                        "function": {"arguments": "", "name": ""},
                        "id": "",
                        "type": "",
                    }
                ),
            }

            # get completion with current history, agent
            completion = self.get_chat_completion(
                agent=active_agent,
                history=history,
                context_variables=context_variables,
                model_override=model_override,
                stream=True,
                debug=debug,
            )

            yield {"delim": "start"}
            for chunk in completion:
                delta = json.loads(chunk.choices[0].delta.json())
                if delta["role"] == "assistant":
                    delta["sender"] = active_agent.name
                yield delta
                delta.pop("role", None)
                delta.pop("sender", None)
                merge_chunk(message, delta)
            yield {"delim": "end"}

            message["tool_calls"] = list(
                message.get("tool_calls", {}).values())
            if not message["tool_calls"]:
                message["tool_calls"] = None
            debug_print(debug, "Received completion:", message)
            history.append(message)

            if not message["tool_calls"] or not execute_tools:
                debug_print(debug, "Ending turn.")
                break

            # convert tool_calls to objects
            tool_calls = []
            for tool_call in message["tool_calls"]:
                function = Function(
                    arguments=tool_call["function"]["arguments"],
                    name=tool_call["function"]["name"],
                )
                tool_call_object = ChatCompletionMessageToolCall(
                    id=tool_call["id"], function=function, type=tool_call["type"]
                )
                tool_calls.append(tool_call_object)

            # handle function calls, updating context_variables, and switching agents
            partial_response = self.handle_tool_calls(
                tool_calls, active_agent.functions, context_variables, debug
            )
            history.extend(partial_response.messages)
            context_variables.update(partial_response.context_variables)
            if partial_response.agent:
                active_agent = partial_response.agent

        yield {
            "response": Response(
                messages=history[init_len:],
                agent=active_agent,
                context_variables=context_variables,
            )
        }

    def run(
        self,
        agent: Agent,
        messages: List,
        context_variables: dict = {},
        model_override: str = None,
        stream: bool = False,
        debug: bool = False,
        max_turns: int = float("inf"),
        execute_tools: bool = True,
    ) -> Response:
        if stream:
            return self.run_and_stream(
                agent=agent,
                messages=messages,
                context_variables=context_variables,
                model_override=model_override,
                debug=debug,
                max_turns=max_turns,
                execute_tools=execute_tools,
            )
        active_agent = agent
        context_variables = copy.deepcopy(context_variables)
        history = copy.deepcopy(messages)
        init_len = len(messages)

        while len(history) - init_len < max_turns and active_agent:

            # get completion with current history, agent
            completion = self.get_chat_completion(
                agent=active_agent,
                history=history,
                context_variables=context_variables,
                model_override=model_override,
                stream=stream,
                debug=debug,
            )
            message = completion.choices[0].message
            debug_print(debug, "Received completion:", message)
            message.sender = active_agent.name
            history.append(
                json.loads(message.model_dump_json())
            )  # to avoid OpenAI types (?)

            if not message.tool_calls or not execute_tools:
                debug_print(debug, "Ending turn.")
                break

            # handle function calls, updating context_variables, and switching agents
            partial_response = self.handle_tool_calls(
                message.tool_calls, active_agent.functions, context_variables, debug
            )
            history.extend(partial_response.messages)
            context_variables.update(partial_response.context_variables)
            if partial_response.agent:
                active_agent = partial_response.agent

        return Response(
            messages=history[init_len:],
            agent=active_agent,
            context_variables=context_variables,
        )



---
File: /swarm/types.py
---

from openai.types.chat import ChatCompletionMessage
from openai.types.chat.chat_completion_message_tool_call import (
    ChatCompletionMessageToolCall,
    Function,
)
from typing import List, Callable, Union, Optional

# Third-party imports
from pydantic import BaseModel

AgentFunction = Callable[[], Union[str, "Agent", dict]]


class Agent(BaseModel):
    name: str = "Agent"
    model: str = "gpt-4o"
    instructions: Union[str, Callable[[], str]] = "You are a helpful agent."
    functions: List[AgentFunction] = []
    tool_choice: str = None
    parallel_tool_calls: bool = True


class Response(BaseModel):
    messages: List = []
    agent: Optional[Agent] = None
    context_variables: dict = {}


class Result(BaseModel):
    """
    Encapsulates the possible return values for an agent function.

    Attributes:
        value (str): The result value as a string.
        agent (Agent): The agent instance, if applicable.
        context_variables (dict): A dictionary of context variables.
    """

    value: str = ""
    agent: Optional[Agent] = None
    context_variables: dict = {}



---
File: /swarm/util.py
---

import inspect
from datetime import datetime


def debug_print(debug: bool, *args: str) -> None:
    if not debug:
        return
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    message = " ".join(map(str, args))
    print(f"\033[97m[\033[90m{timestamp}\033[97m]\033[90m {message}\033[0m")


def merge_fields(target, source):
    for key, value in source.items():
        if isinstance(value, str):
            target[key] += value
        elif value is not None and isinstance(value, dict):
            merge_fields(target[key], value)


def merge_chunk(final_response: dict, delta: dict) -> None:
    delta.pop("role", None)
    merge_fields(final_response, delta)

    tool_calls = delta.get("tool_calls")
    if tool_calls and len(tool_calls) > 0:
        index = tool_calls[0].pop("index")
        merge_fields(final_response["tool_calls"][index], tool_calls[0])


def function_to_json(func) -> dict:
    """
    Converts a Python function into a JSON-serializable dictionary
    that describes the function's signature, including its name,
    description, and parameters.

    Args:
        func: The function to be converted.

    Returns:
        A dictionary representing the function's signature in JSON format.
    """
    type_map = {
        str: "string",
        int: "integer",
        float: "number",
        bool: "boolean",
        list: "array",
        dict: "object",
        type(None): "null",
    }

    try:
        signature = inspect.signature(func)
    except ValueError as e:
        raise ValueError(
            f"Failed to get signature for function {func.__name__}: {str(e)}"
        )

    parameters = {}
    for param in signature.parameters.values():
        try:
            param_type = type_map.get(param.annotation, "string")
        except KeyError as e:
            raise KeyError(
                f"Unknown type annotation {param.annotation} for parameter {param.name}: {str(e)}"
            )
        parameters[param.name] = {"type": param_type}

    required = [
        param.name
        for param in signature.parameters.values()
        if param.default == inspect._empty
    ]

    return {
        "type": "function",
        "function": {
            "name": func.__name__,
            "description": func.__doc__ or "",
            "parameters": {
                "type": "object",
                "properties": parameters,
                "required": required,
            },
        },
    }



---
File: /tests/__init__.py
---




---
File: /tests/mock_client.py
---

from unittest.mock import MagicMock
from swarm.types import ChatCompletionMessage, ChatCompletionMessageToolCall, Function
from openai import OpenAI
from openai.types.chat.chat_completion import ChatCompletion, Choice
import json


def create_mock_response(message, function_calls=[], model="gpt-4o"):
    role = message.get("role", "assistant")
    content = message.get("content", "")
    tool_calls = (
        [
            ChatCompletionMessageToolCall(
                id="mock_tc_id",
                type="function",
                function=Function(
                    name=call.get("name", ""),
                    arguments=json.dumps(call.get("args", {})),
                ),
            )
            for call in function_calls
        ]
        if function_calls
        else None
    )

    return ChatCompletion(
        id="mock_cc_id",
        created=1234567890,
        model=model,
        object="chat.completion",
        choices=[
            Choice(
                message=ChatCompletionMessage(
                    role=role, content=content, tool_calls=tool_calls
                ),
                finish_reason="stop",
                index=0,
            )
        ],
    )


class MockOpenAIClient:
    def __init__(self):
        self.chat = MagicMock()
        self.chat.completions = MagicMock()

    def set_response(self, response: ChatCompletion):
        """
        Set the mock to return a specific response.
        :param response: A ChatCompletion response to return.
        """
        self.chat.completions.create.return_value = response

    def set_sequential_responses(self, responses: list[ChatCompletion]):
        """
        Set the mock to return different responses sequentially.
        :param responses: A list of ChatCompletion responses to return in order.
        """
        self.chat.completions.create.side_effect = responses

    def assert_create_called_with(self, **kwargs):
        self.chat.completions.create.assert_called_with(**kwargs)


# Initialize the mock client
client = MockOpenAIClient()

# Set a sequence of mock responses
client.set_sequential_responses(
    [
        create_mock_response(
            {"role": "assistant", "content": "First response"},
            [
                {
                    "name": "process_refund",
                    "args": {"item_id": "item_123", "reason": "too expensive"},
                }
            ],
        ),
        create_mock_response({"role": "assistant", "content": "Second"}),
    ]
)

# This should return the first mock response
first_response = client.chat.completions.create()
print(
    first_response.choices[0].message
)  # Outputs: role='agent' content='First response'

# This should return the second mock response
second_response = client.chat.completions.create()
print(
    second_response.choices[0].message
)  # Outputs: role='agent' content='Second response'



---
File: /tests/test_core.py
---

import pytest
from swarm import Swarm, Agent
from tests.mock_client import MockOpenAIClient, create_mock_response
from unittest.mock import Mock
import json

DEFAULT_RESPONSE_CONTENT = "sample response content"


@pytest.fixture
def mock_openai_client():
    m = MockOpenAIClient()
    m.set_response(
        create_mock_response({"role": "assistant", "content": DEFAULT_RESPONSE_CONTENT})
    )
    return m


def test_run_with_simple_message(mock_openai_client: MockOpenAIClient):
    agent = Agent()
    # set up client and run
    client = Swarm(client=mock_openai_client)
    messages = [{"role": "user", "content": "Hello, how are you?"}]
    response = client.run(agent=agent, messages=messages)

    # assert response content
    assert response.messages[-1]["role"] == "assistant"
    assert response.messages[-1]["content"] == DEFAULT_RESPONSE_CONTENT


def test_tool_call(mock_openai_client: MockOpenAIClient):
    expected_location = "San Francisco"

    # set up mock to record function calls
    get_weather_mock = Mock()

    def get_weather(location):
        get_weather_mock(location=location)
        return "It's sunny today."

    agent = Agent(name="Test Agent", functions=[get_weather])
    messages = [
        {"role": "user", "content": "What's the weather like in San Francisco?"}
    ]

    # set mock to return a response that triggers function call
    mock_openai_client.set_sequential_responses(
        [
            create_mock_response(
                message={"role": "assistant", "content": ""},
                function_calls=[
                    {"name": "get_weather", "args": {"location": expected_location}}
                ],
            ),
            create_mock_response(
                {"role": "assistant", "content": DEFAULT_RESPONSE_CONTENT}
            ),
        ]
    )

    # set up client and run
    client = Swarm(client=mock_openai_client)
    response = client.run(agent=agent, messages=messages)

    get_weather_mock.assert_called_once_with(location=expected_location)
    assert response.messages[-1]["role"] == "assistant"
    assert response.messages[-1]["content"] == DEFAULT_RESPONSE_CONTENT


def test_execute_tools_false(mock_openai_client: MockOpenAIClient):
    expected_location = "San Francisco"

    # set up mock to record function calls
    get_weather_mock = Mock()

    def get_weather(location):
        get_weather_mock(location=location)
        return "It's sunny today."

    agent = Agent(name="Test Agent", functions=[get_weather])
    messages = [
        {"role": "user", "content": "What's the weather like in San Francisco?"}
    ]

    # set mock to return a response that triggers function call
    mock_openai_client.set_sequential_responses(
        [
            create_mock_response(
                message={"role": "assistant", "content": ""},
                function_calls=[
                    {"name": "get_weather", "args": {"location": expected_location}}
                ],
            ),
            create_mock_response(
                {"role": "assistant", "content": DEFAULT_RESPONSE_CONTENT}
            ),
        ]
    )

    # set up client and run
    client = Swarm(client=mock_openai_client)
    response = client.run(agent=agent, messages=messages, execute_tools=False)
    print(response)

    # assert function not called
    get_weather_mock.assert_not_called()

    # assert tool call is present in last response
    tool_calls = response.messages[-1].get("tool_calls")
    assert tool_calls is not None and len(tool_calls) == 1
    tool_call = tool_calls[0]
    assert tool_call["function"]["name"] == "get_weather"
    assert json.loads(tool_call["function"]["arguments"]) == {
        "location": expected_location
    }


def test_handoff(mock_openai_client: MockOpenAIClient):
    def transfer_to_agent2():
        return agent2

    agent1 = Agent(name="Test Agent 1", functions=[transfer_to_agent2])
    agent2 = Agent(name="Test Agent 2")

    # set mock to return a response that triggers the handoff
    mock_openai_client.set_sequential_responses(
        [
            create_mock_response(
                message={"role": "assistant", "content": ""},
                function_calls=[{"name": "transfer_to_agent2"}],
            ),
            create_mock_response(
                {"role": "assistant", "content": DEFAULT_RESPONSE_CONTENT}
            ),
        ]
    )

    # set up client and run
    client = Swarm(client=mock_openai_client)
    messages = [{"role": "user", "content": "I want to talk to agent 2"}]
    response = client.run(agent=agent1, messages=messages)

    assert response.agent == agent2
    assert response.messages[-1]["role"] == "assistant"
    assert response.messages[-1]["content"] == DEFAULT_RESPONSE_CONTENT



---
File: /tests/test_util.py
---

from swarm.util import function_to_json


def test_basic_function():
    def basic_function(arg1, arg2):
        return arg1 + arg2

    result = function_to_json(basic_function)
    assert result == {
        "type": "function",
        "function": {
            "name": "basic_function",
            "description": "",
            "parameters": {
                "type": "object",
                "properties": {
                    "arg1": {"type": "string"},
                    "arg2": {"type": "string"},
                },
                "required": ["arg1", "arg2"],
            },
        },
    }


def test_complex_function():
    def complex_function_with_types_and_descriptions(
        arg1: int, arg2: str, arg3: float = 3.14, arg4: bool = False
    ):
        """This is a complex function with a docstring."""
        pass

    result = function_to_json(complex_function_with_types_and_descriptions)
    assert result == {
        "type": "function",
        "function": {
            "name": "complex_function_with_types_and_descriptions",
            "description": "This is a complex function with a docstring.",
            "parameters": {
                "type": "object",
                "properties": {
                    "arg1": {"type": "integer"},
                    "arg2": {"type": "string"},
                    "arg3": {"type": "number"},
                    "arg4": {"type": "boolean"},
                },
                "required": ["arg1", "arg2"],
            },
        },
    }



---
File: /pyproject.toml
---

[build-system]
requires = ["setuptools"]
build-backend = "setuptools.build_meta"


---
File: /README.md
---

![Swarm Logo](assets/logo.png)

# Swarm (experimental, educational)

An educational framework exploring ergonomic, lightweight multi-agent orchestration.

> [!WARNING]
> Swarm is currently an experimental sample framework intended to explore ergonomic interfaces for multi-agent systems. It is not intended to be used in production, and therefore has no official support. (This also means we will not be reviewing PRs or issues!)
>
> The primary goal of Swarm is to showcase the handoff & routines patterns explored in the [Orchestrating Agents: Handoffs & Routines](https://cookbook.openai.com/examples/orchestrating_agents) cookbook. It is not meant as a standalone library, and is primarily for educational purposes.

## Install

Requires Python 3.10+

```shell
pip install git+ssh://git@github.com/openai/swarm.git
```

or

```shell
pip install git+https://github.com/openai/swarm.git
```

## Usage

```python
from swarm import Swarm, Agent

client = Swarm()

def transfer_to_agent_b():
    return agent_b


agent_a = Agent(
    name="Agent A",
    instructions="You are a helpful agent.",
    functions=[transfer_to_agent_b],
)

agent_b = Agent(
    name="Agent B",
    instructions="Only speak in Haikus.",
)

response = client.run(
    agent=agent_a,
    messages=[{"role": "user", "content": "I want to talk to agent B."}],
)

print(response.messages[-1]["content"])
```

```
Hope glimmers brightly,
New paths converge gracefully,
What can I assist?
```

## Table of Contents

- [Overview](#overview)
- [Examples](#examples)
- [Documentation](#documentation)
  - [Running Swarm](#running-swarm)
  - [Agents](#agents)
  - [Functions](#functions)
  - [Streaming](#streaming)
- [Evaluations](#evaluations)
- [Utils](#utils)

# Overview

Swarm focuses on making agent **coordination** and **execution** lightweight, highly controllable, and easily testable.

It accomplishes this through two primitive abstractions: `Agent`s and **handoffs**. An `Agent` encompasses `instructions` and `tools`, and can at any point choose to hand off a conversation to another `Agent`.

These primitives are powerful enough to express rich dynamics between tools and networks of agents, allowing you to build scalable, real-world solutions while avoiding a steep learning curve.

> [!NOTE]
> Swarm Agents are not related to Assistants in the Assistants API. They are named similarly for convenience, but are otherwise completely unrelated. Swarm is entirely powered by the Chat Completions API and is hence stateless between calls.

## Why Swarm

Swarm explores patterns that are lightweight, scalable, and highly customizable by design. Approaches similar to Swarm are best suited for situations dealing with a large number of independent capabilities and instructions that are difficult to encode into a single prompt.

The Assistants API is a great option for developers looking for fully-hosted threads and built in memory management and retrieval. However, Swarm is an educational resource for developers curious to learn about multi-agent orchestration. Swarm runs (almost) entirely on the client and, much like the Chat Completions API, does not store state between calls.

# Examples

Check out `/examples` for inspiration! Learn more about each one in its README.

- [`basic`](examples/basic): Simple examples of fundamentals like setup, function calling, handoffs, and context variables
- [`triage_agent`](examples/triage_agent): Simple example of setting up a basic triage step to hand off to the right agent
- [`weather_agent`](examples/weather_agent): Simple example of function calling
- [`airline`](examples/airline): A multi-agent setup for handling different customer service requests in an airline context.
- [`support_bot`](examples/support_bot): A customer service bot which includes a user interface agent and a help center agent with several tools
- [`personal_shopper`](examples/personal_shopper): A personal shopping agent that can help with making sales and refunding orders

# Documentation

![Swarm Diagram](assets/swarm_diagram.png)

## Running Swarm

Start by instantiating a Swarm client (which internally just instantiates an `OpenAI` client).

```python
from swarm import Swarm

client = Swarm()
```

### `client.run()`

Swarm's `run()` function is analogous to the `chat.completions.create()` function in the Chat Completions API – it takes `messages` and returns `messages` and saves no state between calls. Importantly, however, it also handles Agent function execution, hand-offs, context variable references, and can take multiple turns before returning to the user.

At its core, Swarm's `client.run()` implements the following loop:

1. Get a completion from the current Agent
2. Execute tool calls and append results
3. Switch Agent if necessary
4. Update context variables, if necessary
5. If no new function calls, return

#### Arguments

| Argument              | Type    | Description                                                                                                                                            | Default        |
| --------------------- | ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ | -------------- |
| **agent**             | `Agent` | The (initial) agent to be called.                                                                                                                      | (required)     |
| **messages**          | `List`  | A list of message objects, identical to [Chat Completions `messages`](https://platform.openai.com/docs/api-reference/chat/create#chat-create-messages) | (required)     |
| **context_variables** | `dict`  | A dictionary of additional context variables, available to functions and Agent instructions                                                            | `{}`           |
| **max_turns**         | `int`   | The maximum number of conversational turns allowed                                                                                                     | `float("inf")` |
| **model_override**    | `str`   | An optional string to override the model being used by an Agent                                                                                        | `None`         |
| **execute_tools**     | `bool`  | If `False`, interrupt execution and immediately returns `tool_calls` message when an Agent tries to call a function                                    | `True`         |
| **stream**            | `bool`  | If `True`, enables streaming responses                                                                                                                 | `False`        |
| **debug**             | `bool`  | If `True`, enables debug logging                                                                                                                       | `False`        |

Once `client.run()` is finished (after potentially multiple calls to agents and tools) it will return a `Response` containing all the relevant updated state. Specifically, the new `messages`, the last `Agent` to be called, and the most up-to-date `context_variables`. You can pass these values (plus new user messages) in to your next execution of `client.run()` to continue the interaction where it left off – much like `chat.completions.create()`. (The `run_demo_loop` function implements an example of a full execution loop in `/swarm/repl/repl.py`.)

#### `Response` Fields

| Field                 | Type    | Description                                                                                                                                                                                                                                                                  |
| --------------------- | ------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **messages**          | `List`  | A list of message objects generated during the conversation. Very similar to [Chat Completions `messages`](https://platform.openai.com/docs/api-reference/chat/create#chat-create-messages), but with a `sender` field indicating which `Agent` the message originated from. |
| **agent**             | `Agent` | The last agent to handle a message.                                                                                                                                                                                                                                          |
| **context_variables** | `dict`  | The same as the input variables, plus any changes.                                                                                                                                                                                                                           |

## Agents

An `Agent` simply encapsulates a set of `instructions` with a set of `functions` (plus some additional settings below), and has the capability to hand off execution to another `Agent`.

While it's tempting to personify an `Agent` as "someone who does X", it can also be used to represent a very specific workflow or step defined by a set of `instructions` and `functions` (e.g. a set of steps, a complex retrieval, single step of data transformation, etc). This allows `Agent`s to be composed into a network of "agents", "workflows", and "tasks", all represented by the same primitive.

## `Agent` Fields

| Field            | Type                     | Description                                                                   | Default                      |
| ---------------- | ------------------------ | ----------------------------------------------------------------------------- | ---------------------------- |
| **name**         | `str`                    | The name of the agent.                                                        | `"Agent"`                    |
| **model**        | `str`                    | The model to be used by the agent.                                            | `"gpt-4o"`                   |
| **instructions** | `str` or `func() -> str` | Instructions for the agent, can be a string or a callable returning a string. | `"You are a helpful agent."` |
| **functions**    | `List`                   | A list of functions that the agent can call.                                  | `[]`                         |
| **tool_choice**  | `str`                    | The tool choice for the agent, if any.                                        | `None`                       |

### Instructions

`Agent` `instructions` are directly converted into the `system` prompt of a conversation (as the first message). Only the `instructions` of the active `Agent` will be present at any given time (e.g. if there is an `Agent` handoff, the `system` prompt will change, but the chat history will not.)

```python
agent = Agent(
   instructions="You are a helpful agent."
)
```

The `instructions` can either be a regular `str`, or a function that returns a `str`. The function can optionally receive a `context_variables` parameter, which will be populated by the `context_variables` passed into `client.run()`.

```python
def instructions(context_variables):
   user_name = context_variables["user_name"]
   return f"Help the user, {user_name}, do whatever they want."

agent = Agent(
   instructions=instructions
)
response = client.run(
   agent=agent,
   messages=[{"role":"user", "content": "Hi!"}],
   context_variables={"user_name":"John"}
)
print(response.messages[-1]["content"])
```

```
Hi John, how can I assist you today?
```

## Functions

- Swarm `Agent`s can call python functions directly.
- Function should usually return a `str` (values will be attempted to be cast as a `str`).
- If a function returns an `Agent`, execution will be transferred to that `Agent`.
- If a function defines a `context_variables` parameter, it will be populated by the `context_variables` passed into `client.run()`.

```python
def greet(context_variables, language):
   user_name = context_variables["user_name"]
   greeting = "Hola" if language.lower() == "spanish" else "Hello"
   print(f"{greeting}, {user_name}!")
   return "Done"

agent = Agent(
   functions=[greet]
)

client.run(
   agent=agent,
   messages=[{"role": "user", "content": "Usa greet() por favor."}],
   context_variables={"user_name": "John"}
)
```

```
Hola, John!
```

- If an `Agent` function call has an error (missing function, wrong argument, error) an error response will be appended to the chat so the `Agent` can recover gracefully.
- If multiple functions are called by the `Agent`, they will be executed in that order.

### Handoffs and Updating Context Variables

An `Agent` can hand off to another `Agent` by returning it in a `function`.

```python
sales_agent = Agent(name="Sales Agent")

def transfer_to_sales():
   return sales_agent

agent = Agent(functions=[transfer_to_sales])

response = client.run(agent, [{"role":"user", "content":"Transfer me to sales."}])
print(response.agent.name)
```

```
Sales Agent
```

It can also update the `context_variables` by returning a more complete `Result` object. This can also contain a `value` and an `agent`, in case you want a single function to return a value, update the agent, and update the context variables (or any subset of the three).

```python
sales_agent = Agent(name="Sales Agent")

def talk_to_sales():
   print("Hello, World!")
   return Result(
       value="Done",
       agent=sales_agent,
       context_variables={"department": "sales"}
   )

agent = Agent(functions=[talk_to_sales])

response = client.run(
   agent=agent,
   messages=[{"role": "user", "content": "Transfer me to sales"}],
   context_variables={"user_name": "John"}
)
print(response.agent.name)
print(response.context_variables)
```

```
Sales Agent
{'department': 'sales', 'user_name': 'John'}
```

> [!NOTE]
> If an `Agent` calls multiple functions to hand-off to an `Agent`, only the last handoff function will be used.

### Function Schemas

Swarm automatically converts functions into a JSON Schema that is passed into Chat Completions `tools`.

- Docstrings are turned into the function `description`.
- Parameters without default values are set to `required`.
- Type hints are mapped to the parameter's `type` (and default to `string`).
- Per-parameter descriptions are not explicitly supported, but should work similarly if just added in the docstring. (In the future docstring argument parsing may be added.)

```python
def greet(name, age: int, location: str = "New York"):
   """Greets the user. Make sure to get their name and age before calling.

   Args:
      name: Name of the user.
      age: Age of the user.
      location: Best place on earth.
   """
   print(f"Hello {name}, glad you are {age} in {location}!")
```

```javascript
{
   "type": "function",
   "function": {
      "name": "greet",
      "description": "Greets the user. Make sure to get their name and age before calling.\n\nArgs:\n   name: Name of the user.\n   age: Age of the user.\n   location: Best place on earth.",
      "parameters": {
         "type": "object",
         "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer"},
            "location": {"type": "string"}
         },
         "required": ["name", "age"]
      }
   }
}
```

## Streaming

```python
stream = client.run(agent, messages, stream=True)
for chunk in stream:
   print(chunk)
```

Uses the same events as [Chat Completions API streaming](https://platform.openai.com/docs/api-reference/streaming). See `process_and_print_streaming_response` in `/swarm/repl/repl.py` as an example.

Two new event types have been added:

- `{"delim":"start"}` and `{"delim":"end"}`, to signal each time an `Agent` handles a single message (response or function call). This helps identify switches between `Agent`s.
- `{"response": Response}` will return a `Response` object at the end of a stream with the aggregated (complete) response, for convenience.

# Evaluations

Evaluations are crucial to any project, and we encourage developers to bring their own eval suites to test the performance of their swarms. For reference, we have some examples for how to eval swarm in the `airline`, `weather_agent` and `triage_agent` quickstart examples. See the READMEs for more details.

# Utils

Use the `run_demo_loop` to test out your swarm! This will run a REPL on your command line. Supports streaming.

```python
from swarm.repl import run_demo_loop
...
run_demo_loop(agent, stream=True)
```

# Core Contributors

- Ilan Bigio - [ibigio](https://github.com/ibigio)
- James Hills - [jhills20](https://github.com/jhills20)
- Shyamal Anadkat - [shyamal-anadkat](https://github.com/shyamal-anadkat)
- Charu Jaiswal - [charuj](https://github.com/charuj)
- Colin Jarvis - [colin-openai](https://github.com/colin-openai)
- Katia Gil Guzman - [katia-openai](https://github.com/katia-openai)



---
File: /SECURITY.md
---

# Security Policy

For a more in-depth look at our security policy, please check out our [Coordinated Vulnerability Disclosure Policy](https://openai.com/security/disclosure/#:~:text=Disclosure%20Policy,-Security%20is%20essential&text=OpenAI%27s%20coordinated%20vulnerability%20disclosure%20policy,expect%20from%20us%20in%20return.).

Our PGP key can located [at this address.](https://cdn.openai.com/security.txt)



---
File: /setup.cfg
---

[metadata]
name = swarm
version = 0.1.0
author = OpenAI Solutions
description = A lightweight, stateless multi-agent orchestration framework.
long_description = file: README.md
long_description_content_type = text/markdown
license = MIT

[options]
packages = find:
zip_safe = True
include_package_data = True
install_requires =
    numpy
    openai>=1.33.0
    pytest
    requests
    tqdm
    pre-commit
    instructor
python_requires = >=3.10

[tool.autopep8]
max_line_length = 120
ignore = E501,W6
in-place = true
recursive = true
aggressive = 3

