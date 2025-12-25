# Prompt Caching

> Store and reuse previously processed prompts to reduce latency and increase response times for similar or repeated queries.

This feature is designed to significantly reduce Time to First Token (TTFT) and improve responsiveness for long-context workloads, such as multi-turn conversations, RAG (Retrieval Augmented Generation), and agentic workflows.

<Check>
  Prompt caching is enabled by default for the following models:

  * [`zai-glm-4.6`](/models/zai-glm-46)
  * [`gpt-oss-120b`](/models/openai-oss)
  * [`qwen-3-235b-a22b-instruct-2507`](/models/qwen-3-235b-2507)
  * [`qwen-3-32b`](/models/qwen-3-32b)
  * [`llama-3.3-70b`](/models/llama-33-70b)
</Check>

## How It Works

Unlike other providers that require manual cache breakpoints or header modifications, Cerebras Prompt Caching works automatically on all supported API requests. No code changes are required.

1. **Prefix Matching**: When you send a request, the system analyzes the beginning of your prompt (the prefix). This includes system prompts, tool definitions, and few-shot examples.

2. **Block-Based Caching**: The system processes prompts in blocks (typically 100–600 tokens). If a block matches a segment stored in our ephemeral memory from a recent request within your organization, the computation is reused.

3. **Cache Hit**: Reusing cached blocks skips the processing phase for those tokens, resulting in lower latency.

4. **Cache Miss**: If no match is found, the prompt is processed as normal, and the prefix is stored in the cache for potential future matches.

5. **Automatic Expiration**: Cached data is ephemeral. We guarantee a Time-To-Live (TTL) of 5 minutes, though caches may persist up to 1 hour depending on system load.

<Note>
  To get a cache hit, the entire beginning of your prompt must match *exactly* with a previously cached prefix. Even a single character difference in the first token will result in a cache miss for that block and all subsequent blocks.
</Note>

## Example: Multi-Turn Conversation with Tool Calling

In this scenario, a shopping assistant helps users check order status and cancel orders using two tools: `get_order_status` and `cancel_order`. The system message and tool definitions remain constant across turns and are cached, while the conversation progresses naturally.

<CodeGroup>
  ```python Python expandable theme={null}
  import os
  import json
  from cerebras.cloud.sdk import Cerebras

  client = Cerebras(api_key=os.environ.get("CEREBRAS_API_KEY"))

  # Mock order database
  ORDERS = {
      "ORD-123456": {"status": "processing", "eta_days": 5},
  }

  def get_order_status(order_id: str):
      """Look up an order's status"""
      order = ORDERS.get(order_id)
      if not order:
          return {"error": "Order not found"}
      return {"order_id": order_id, "status": order["status"], "eta_days": order.get("eta_days")}

  def cancel_order(order_id: str):
      """Cancel an order"""
      order = ORDERS.get(order_id)
      if not order:
          return {"error": "Order not found"}
      if order["status"] in ["shipped", "delivered"]:
          return {"error": f"Cannot cancel - order already {order['status']}"}
      
      order["status"] = "cancelled"
      order.pop("eta_days", None)
      return {"order_id": order_id, "status": "cancelled"}

  tools = [
      {
          "type": "function",
          "function": {
              "name": "get_order_status",
              "description": "Look up an order status by order ID",
              "parameters": {
                  "type": "object",
                  "properties": {
                      "order_id": {"type": "string", "description": "Order ID (e.g., ORD-123456)"}
                  },
                  "required": ["order_id"]
              },
              "strict": True
          }
      },
      {
          "type": "function",
          "function": {
              "name": "cancel_order",
              "description": "Cancel an order by order ID",
              "parameters": {
                  "type": "object",
                  "properties": {
                      "order_id": {"type": "string", "description": "Order ID (e.g., ORD-123456)"}
                  },
                  "required": ["order_id"]
              },
              "strict": True
          }
      }
  ]

  available_functions = {
      "get_order_status": get_order_status,
      "cancel_order": cancel_order
  }

  messages = [
      {"role": "system", "content": "You are a shopping assistant. Help users check order status and cancel orders."},
      {"role": "user", "content": "Where is my order ORD-123456?"}
  ]

  # Turn 1 - creates cache
  response = client.chat.completions.create(model="qwen-3-32b", messages=messages, tools=tools)
  print("Turn 1 usage:", response.usage)

  msg = response.choices[0].message
  messages.append(msg.model_dump())

  if msg.tool_calls:
      for call in msg.tool_calls:
          func = available_functions[call.function.name]
          result = func(**json.loads(call.function.arguments))
          messages.append({"role": "tool", "tool_call_id": call.id, "content": json.dumps(result)})
      
      response = client.chat.completions.create(model="qwen-3-32b", messages=messages, tools=tools)
      messages.append(response.choices[0].message.model_dump())
      print("Turn 1 response:", response.choices[0].message.content)

  # Turn 2 - uses cache
  messages.append({"role": "user", "content": "Please cancel it, I ordered by mistake."})
  response = client.chat.completions.create(model="qwen-3-32b", messages=messages, tools=tools)
  print("\nTurn 2 usage:", response.usage)

  msg = response.choices[0].message
  messages.append(msg.model_dump())

  if msg.tool_calls:
      for call in msg.tool_calls:
          func = available_functions[call.function.name]
          result = func(**json.loads(call.function.arguments))
          messages.append({"role": "tool", "tool_call_id": call.id, "content": json.dumps(result)})
      
      response = client.chat.completions.create(model="qwen-3-32b", messages=messages, tools=tools)
      print("Turn 2 response:", response.choices[0].message.content)
  ```

  ```bash cURL expandable theme={null}
  #!/bin/bash

  API_KEY="${CEREBRAS_API_KEY}"
  BASE_URL="https://api.cerebras.ai/v1"

  if [ -z "$API_KEY" ]; then
      echo "Error: CEREBRAS_API_KEY environment variable is not set"
      exit 1
  fi

  TOOLS='[
    {
      "type": "function",
      "function": {
        "name": "get_order_status",
        "description": "Look up an order status by order ID",
        "parameters": {
          "type": "object",
          "properties": {
            "order_id": {"type": "string", "description": "Order ID (e.g., ORD-123456)"}
          },
          "required": ["order_id"]
        },
        "strict": true
      }
    },
    {
      "type": "function",
      "function": {
        "name": "cancel_order",
        "description": "Cancel an order by order ID",
        "parameters": {
          "type": "object",
          "properties": {
            "order_id": {"type": "string", "description": "Order ID (e.g., ORD-123456)"}
          },
          "required": ["order_id"]
        },
        "strict": true
      }
    }
  ]'

  SYSTEM="You are a shopping assistant. Help users check order status and cancel orders."

  echo "=== Turn 1 (Creates Cache) ==="

  curl -s -X POST "$BASE_URL/chat/completions" \
    -H "Authorization: Bearer $API_KEY" \
    -H "Content-Type: application/json" \
    -d "$(jq -n --arg sys "$SYSTEM" --argjson tools "$TOOLS" '{
      model: "qwen-3-32b",
      messages: [{role: "system", content: $sys}, {role: "user", content: "Where is my order ORD-123456?"}],
      tools: $tools
    }')" | jq '{content: .choices[0].message.content, usage: .usage}'

  echo ""
  echo "=== Turn 2 (Uses Cache) ==="

  curl -s -X POST "$BASE_URL/chat/completions" \
    -H "Authorization: Bearer $API_KEY" \
    -H "Content-Type: application/json" \
    -d "$(jq -n --arg sys "$SYSTEM" --argjson tools "$TOOLS" '{
      model: "qwen-3-32b",
      messages: [
        {role: "system", content: $sys},
        {role: "user", content: "Where is my order ORD-123456?"},
        {role: "assistant", content: "Your order ORD-123456 is currently processing with an estimated delivery in 5 days."},
        {role: "user", content: "Please cancel it, I ordered by mistake."}
      ],
      tools: $tools
    }')" | jq '{content: .choices[0].message.content, usage: .usage}'
  ```
</CodeGroup>

During each turn, the system automatically caches the longest matching prefix from previous requests. In this example:

* **System message**: The shopping assistant instructions remain identical across all turns
* **Tool definitions**: Both order management tool schemas (including parameters and descriptions) stay constant
* **Conversation history**: Previous user messages, assistant responses, and tool results are all cached as the conversation grows

Only the new content at the end of each request requires fresh processing:

* New user messages (the latest question)
* New tool execution results
* The model's reasoning and decision-making for the current turn

As the conversation grows, the cache hit rate increases dramatically. The static prefix (system + tools) remains cached, and the expanding conversation history also gets cached, meaning only the newest user message and the model's fresh response require full processing.

## Structuring Prompts for Caching

To maximize cache hits and minimize latency, organize your prompts with static content first and dynamic content last.

The system caches prompts from the **beginning** of the message. If you place dynamic content (like a timestamp or a unique User ID) at the start of the prompt, the prefix will differ for every request and the cache will never be triggered.

<Steps>
  <Step title="Static Content First">
    Place content that remains the same across multiple requests at the beginning:

    * System instructions ("You are a helpful assistant...")
    * Tool definitions and schemas
    * Few-shot examples
    * Large context documents (e.g., a legal agreement or code base)
  </Step>

  <Step title="Dynamic Content Last">
    Place content that changes with each request at the end:

    * User-specific questions
    * Session variables
    * Timestamps
  </Step>
</Steps>

<Tabs>
  <Tab title="Optimized (Cache Hit)">
    The "You are a coding assistant..." instruction block remains static and can be cached in subsequent requests. Only the short timestamp and user query are processed fresh.

    ```json  theme={null}
    [
      {
        "role": "system",
        "content": "You are a coding assistant... Current Time: 12:01 PM"
      },
      {
        "role": "user",
        "content": "Debug this code."
      }
    ]
    ```

    <Check>
      **Result:** The static portion of the system prompt is cached. Subsequent requests reuse the cache and only process the timestamp and user query.
    </Check>
  </Tab>

  <Tab title="Inefficient (Cache Miss)">
    In this example, the time is included at the start of the system instructions. Because the time changes every minute, the prefix never matches. Subsequent requests will always be fully processed.

    ```json  theme={null}
    [
      {
        "role": "system",
        "content": "Current Time: 12:01 PM. You are a coding assistant..."
      },
      {
        "role": "user",
        "content": "Debug this code."
      }
    ]
    ```

    <Warning>
      **Result:** Cache miss on every request because the timestamp changes the prefix.
    </Warning>
  </Tab>
</Tabs>

## Track Cache Usage

Verify if your requests are hitting the cache by viewing the `cached_tokens` field within the [`usage.prompt_token_details`](/api-reference/chat-completions#param-prompt-tokens-details) response object. This indicates the number of prompt tokens that were found in the cache.

```json  theme={null}
"usage": {
  "prompt_tokens": 3000,
  "completion_tokens": 150,
  "total_tokens": 3150,
  "prompt_tokens_details": {
    "cached_tokens": 2800
  }
}
```

In this example, 2,800 of the 3,000 prompt tokens were served from the cache, resulting in significantly faster processing.

Additionally, log in to [cloud.cerebras.ai](https://cloud.cerebras.ai) and click **Analytics** to track your cache usage.

## FAQs

<AccordionGroup>
  <Accordion title="Do cached tokens count toward rate limits?">
    Yes. All cached tokens contribute to your standard Tokens Per Minute (TPM) rate limits.

    **Calculation:** `cached_tokens + input_tokens` (fresh) = Total TPM usage for that request.
  </Accordion>

  <Accordion title="How are cached tokens priced?">
    There is no additional fee for using prompt caching. Input tokens, whether served from the cache or processed fresh, are billed at the standard input token rate for the respective model.
  </Accordion>

  <Accordion title="I'm sending the same request but not seeing it being cached. Why is that?">
    There are three common reasons for a cache miss on identical requests:

    1. **Block Size:** We cache in "blocks" (typically 100-600 tokens). If a request or prefix is shorter than the minimum block size, it may not be cached.

    2. **Data Center Routing:** While we make a best effort to route you to the same data center, traffic profiles may occasionally route you to a different location where your cache does not exist.

    3. **TTL Expiration:** If requests are sent more than 5 minutes apart, the cache may have been evicted.
  </Accordion>

  <Accordion title="Is prompt caching enabled for all customers?">
    Yes, prompt caching is automatically enabled for all users for the supported models.
  </Accordion>

  <Accordion title="Is prompt caching secure?">
    Yes, it is fully ZDR-compliant. All cached context remains ephemeral in memory and never persisted. Cached tokens are stored in key-value stores colocated in the same data center as the model instance serving your traffic.
  </Accordion>

  <Accordion title="How is data privacy maintained for caches?">
    Prompt caches are never shared between organizations. Only members of your organization can benefit from caches created by identical prompts within your team.
  </Accordion>

  <Accordion title="Does prompt caching affect output quality or speed?">
    Caching only affects the input processing phase (how we read your prompt). The output generation phase remains exactly the same speed and quality. You will receive the same quality response, just with faster prompt processing.
  </Accordion>

  <Accordion title="Can I manually clear the cache?">
    No manual cache management is required or available. The system automatically manages cache eviction based on the TTL (5 minutes to 1 hour).
  </Accordion>

  <Accordion title="What are the TTL guarantees?">
    Guaranteed TTL is 5 minutes, but up to 1 hour max depending on system load.
  </Accordion>

  <Accordion title="How can I tell when caching is working?">
    Check the `usage.prompt_tokens_details.cached_tokens` field in your API response. When it's greater than 0, caching was used for that request.

    Additionally, log in to [cloud.cerebras.ai](https://cloud.cerebras.ai) and click **Analytics** to track your cache usage.
  </Accordion>
</AccordionGroup>


---

> To find navigation and other pages in this documentation, fetch the llms.txt file at: https://inference-docs.cerebras.ai/llms.txt